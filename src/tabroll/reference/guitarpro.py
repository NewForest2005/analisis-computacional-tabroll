"""Parser de partituras Guitar Pro 8 para referencias de análisis.

Los archivos ``.gp`` de Guitar Pro 8 son ZIP que contienen
``Content/score.gpif``. Este módulo convierte ese XML en eventos musicales
serializables, sin depender de librerías de audio ni de Guitar Pro.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import zipfile
import xml.etree.ElementTree as ET


NOTE_VALUES = {
    "64th": 0.0625,
    "32nd": 0.125,
    "16th": 0.25,
    "Eighth": 0.5,
    "Quarter": 1.0,
    "Half": 2.0,
    "Whole": 4.0,
}


@dataclass(frozen=True)
class Pitch:
    """Altura de una nota y su posible bend expresado en semitonos."""

    name: str
    midi: int | float
    bend_value: float = 0.0
    bend_destination_value: float = 0.0
    bend_semitones: float = 0.0
    midi_with_bend: float = 0.0


@dataclass(frozen=True)
class NoteEvent:
    """Nota de una pista dentro de la línea temporal de la partitura."""

    master_bar: int
    bar_id: str
    voice: int
    beat: int
    onset_in_bar: float
    onset_beats: float
    duration_beats: float
    pitch: Pitch
    fret: int | None
    string: int | None
    articulation: int


@dataclass(frozen=True)
class MasterBar:
    """Compás de la partitura, compartido por las pistas."""

    number: int
    time_signature: str
    start_beat: float
    duration_beats: float
    bar_ids: tuple[str, ...]


@dataclass
class Track:
    """Pista Guitar Pro y sus eventos de nota."""

    id: str
    name: str
    events: list[NoteEvent]


@dataclass
class GuitarProScore:
    """Partitura completa extraída de un archivo ``.gp``."""

    source: str
    gp_version: str
    title: str
    subtitle: str
    master_bars: list[MasterBar]
    tracks: list[Track]

    def to_dict(self) -> dict[str, Any]:
        """Devuelve una representación compatible con JSON."""
        return {"format": "Guitar Pro GPIF", **asdict(self)}


def _text(element: ET.Element | None, path: str, default: str = "") -> str:
    if element is None:
        return default
    child = element.find(path)
    return (child.text or default).strip() if child is not None else default


def _number(element: ET.Element | None, path: str, default: float | None = None) -> float | None:
    value = _text(element, path)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _rhythm_duration(rhythm: ET.Element) -> float:
    name = _text(rhythm, "NoteValue")
    try:
        duration = NOTE_VALUES[name]
    except KeyError as exc:
        raise ValueError(f"Ritmo Guitar Pro no soportado: {name!r}") from exc
    dot = rhythm.find("AugmentationDot")
    if dot is not None:
        dots = int(dot.attrib.get("count", "1"))
        duration *= 2.0 - 0.5 ** dots
    for tag in ("PrimaryTuplet", "SecondaryTuplet"):
        tuplet = rhythm.find(tag)
        if tuplet is not None:
            duration *= float(tuplet.attrib["den"]) / float(tuplet.attrib["num"])
    return duration


def _read_root(path: Path) -> ET.Element:
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        with zipfile.ZipFile(path) as archive:
            try:
                data = archive.read("Content/score.gpif")
            except KeyError as exc:
                raise ValueError(f"{path} no contiene Content/score.gpif") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{path} no es un archivo .gp válido") from exc
    return ET.fromstring(data)


def _parse_pitch(note: ET.Element) -> Pitch | None:
    properties = note.find("Properties")
    pitch_element = None
    if properties is not None:
        for prop in properties.findall("Property"):
            if prop.attrib.get("name") == "ConcertPitch":
                pitch_element = prop.find("Pitch")
                break
    midi = _number(note, "Properties/Property[@name='Midi']/Number")
    if pitch_element is None or midi is None:
        return None

    bend = note.find("Properties/Property[@name='Bended']")
    origin = _number(note, "Properties/Property[@name='BendOriginValue']/Float", 0.0) or 0.0
    destination = _number(note, "Properties/Property[@name='BendDestinationValue']/Float", origin) or origin
    bend_semitones = origin / 50.0 if bend is not None else 0.0

    return Pitch(
        name=f"{_text(pitch_element, 'Step')}{_text(pitch_element, 'Accidental')}{_text(pitch_element, 'Octave')}",
        midi=int(midi) if midi.is_integer() else midi,
        bend_value=origin if bend is not None else 0.0,
        bend_destination_value=destination if bend is not None else 0.0,
        bend_semitones=bend_semitones,
        midi_with_bend=midi + bend_semitones,
    )


def parse_score(path: str | Path) -> GuitarProScore:
    """Lee una partitura Guitar Pro y devuelve objetos musicales tipados.

    ``onset_beats`` y ``duration_beats`` se expresan en negras desde el
    comienzo del primer compás. La pista conserva el número de voz y la
    posición relativa dentro del compás para permitir alineaciones futuras.
    """
    source = Path(path).expanduser().resolve()
    root = _read_root(source)
    score = root.find("Score")
    tracks_xml = {x.attrib["id"]: x for x in root.findall("./Tracks/Track")}
    bars = {x.attrib["id"]: x for x in root.findall("./Bars/Bar")}
    voices = {x.attrib["id"]: x for x in root.findall("./Voices/Voice")}
    beats = {x.attrib["id"]: x for x in root.findall("./Beats/Beat")}
    notes = {x.attrib["id"]: x for x in root.findall("./Notes/Note")}
    rhythms = {x.attrib["id"]: x for x in root.findall("./Rhythms/Rhythm")}
    master_bars_xml = root.findall("./MasterBars/MasterBar")

    tracks = [Track(track_id, _text(track, "Name"), []) for track_id, track in tracks_xml.items()]
    track_by_id = {track.id: track for track in tracks}
    master_bars: list[MasterBar] = []
    absolute_beat = 0.0

    for master_number, master in enumerate(master_bars_xml, start=1):
        bar_ids = tuple(_text(master, "Bars").split())
        time_signature = _text(master, "Time", "4/4")
        try:
            numerator, denominator = (int(value) for value in time_signature.split("/", 1))
            duration = numerator * 4.0 / denominator
        except ValueError:
            time_signature, duration = "4/4", 4.0

        master_bars.append(MasterBar(master_number, time_signature, absolute_beat, duration, bar_ids))
        for position, track_id in enumerate(tracks_xml):
            if position >= len(bar_ids) or bar_ids[position] not in bars:
                continue
            bar = bars[bar_ids[position]]
            track = track_by_id[track_id]
            for voice_id in _text(bar, "Voices").split():
                if voice_id == "-1" or voice_id not in voices:
                    continue
                voice_beat = 0.0
                for beat_number, beat_id in enumerate(_text(voices[voice_id], "Beats").split()):
                    beat = beats.get(beat_id)
                    if beat is None:
                        continue
                    rhythm_ref = beat.find("Rhythm")
                    rhythm = rhythms.get(rhythm_ref.attrib.get("ref")) if rhythm_ref is not None else None
                    beat_duration = _rhythm_duration(rhythm) if rhythm is not None else 0.5
                    for note_id in _text(beat, "Notes").split():
                        note = notes.get(note_id)
                        pitch = _parse_pitch(note) if note is not None else None
                        if note is None or pitch is None:
                            continue
                        fret = _number(note, "Properties/Property[@name='Fret']/Fret")
                        string = _number(note, "Properties/Property[@name='String']/String")
                        articulation = _number(note, "InstrumentArticulation", 0) or 0
                        track.events.append(
                            NoteEvent(
                                master_bar=master_number,
                                bar_id=bar_ids[position],
                                voice=int(voice_id),
                                beat=beat_number,
                                onset_in_bar=voice_beat,
                                onset_beats=absolute_beat + voice_beat,
                                duration_beats=beat_duration,
                                pitch=pitch,
                                fret=int(fret) if fret is not None else None,
                                string=int(string) if string is not None else None,
                                articulation=int(articulation),
                            )
                        )
                    voice_beat += beat_duration
        absolute_beat += duration

    for track in tracks:
        track.events.sort(key=lambda event: (event.onset_beats, event.voice))
    return GuitarProScore(
        source=str(source),
        gp_version=_text(root, "GPVersion"),
        title=_text(score, "Title"),
        subtitle=_text(score, "SubTitle"),
        master_bars=master_bars,
        tracks=tracks,
    )


def parse_gp(path: str | Path) -> dict[str, Any]:
    """Atajo compatible con JSON: devuelve ``parse_score(path).to_dict()``."""
    return parse_score(path).to_dict()
