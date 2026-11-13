import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
NB = json.loads((ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb").read_text(encoding="utf-8"))
CODE = ["".join(c["source"]) for c in NB["cells"] if c["cell_type"] == "code"]
CANCIONES = ("sarniezz", "mata zyklek", "mata_zyklek", "fabienk", "utzp", "uztp", "yor zarad", "yor_zarad")


def test_ninguna_celda_lee_la_partitura():
    for s in CODE:
        assert not re.search(r"references|_gp\.json|GUIAR_CON_GP|align_gp_audio|select_melody_track", s)


def test_solo_la_celda_que_elige_la_cancion_nombra_canciones():
    for s in CODE:
        if re.search(r"^SONG\s*=", s, re.M):
            continue
        assert not any(n in s.lower() for n in CANCIONES)


def test_demucs_separa_con_semilla_fija():
    s = next(s for s in CODE if s.startswith("def separate_stems("))
    assert "semilla=0" in s.splitlines()[0]
    assert s.index("random.seed(semilla)") < s.index("apply_model(model")


def test_huella_es_el_sha256_del_archivo(tmp_path):
    spec = importlib.util.spec_from_file_location("run_song", ROOT / "scripts" / "run_song.py")
    run_song = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_song)
    pista = tmp_path / "pista.mp3"
    pista.write_bytes(bytes(range(256)) * 9000)
    assert run_song.huella(pista) == hashlib.sha256(pista.read_bytes()).hexdigest()
    assert run_song.huella(None) is None
