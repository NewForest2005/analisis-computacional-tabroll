# Separación de guitarra y bajo con BS-RoFormer SW

El cuaderno separa guitarra y bajo con Demucs `htdemucs_6s` (semilla 0). Esta nota documenta una alternativa,
**BS-RoFormer SW**, que en las métricas públicas de MVSEP separa mejor las dos pistas que nos interesan, y cómo
se integró al proyecto para compararla con Demucs sobre nuestro propio material.

## El modelo

| | BS-RoFormer SW | Demucs `htdemucs_6s` (línea base) |
|---|---|---|
| Arquitectura | BS-RoFormer, ~0.2 B parámetros | Híbrido transformer |
| Pistas | bass, drums, other, vocals, guitar, piano | 6 pistas |
| SDR guitarra (MVSEP) | 9.05 | 5.22 |
| SDR bajo (MVSEP) | 14.62 | — (HTDemucs4: 12.52) |
| Licencia | **desconocida** | MIT |

- Checkpoint: `BS-Rofo-SW-Fixed.ckpt`, 699 412 152 B, SHA-256
  `24e7d35ee9c64415673d3fd33e06a67cac2c103c5df6267ba1576459c775916e`
  (hoy en `huggingface.co/enerjazzer/BS-ROFO-SW-Fixed`; la cuenta original desapareció).
  audio-separator lo distribuye como `BS-Roformer-SW.ckpt`; el manifiesto de cada separación registra el SHA-256
  del archivo que se usó y si coincide con el de arriba.
- «SW» significa *shared weights*. Nadie con nombre público figura como entrenador y los pesos no tienen licencia
  declarada: se usa solo con fines académicos y se cita como «BS-RoFormer SW (shared weights), checkpoint
  BS-Rofo-SW-Fixed, SHA-256 24e7d35e…».
- Las métricas de MVSEP son sobre mezclas comerciales, no sobre guitarra en 24-EDO con looper. Un SDR más alto no
  garantiza menos errores de altura en cuartos de tono; por eso la comparación se hace con nuestras partituras
  corregidas (`evaluar_melodia.py`).

## Cómo está integrado

```text
Angine de Poitrine Audios/<Canción>.mp3
        │  scripts/separar_roformer.py   (entorno .venv-rof)
        ▼
pistas_roformer/<Canción>_guitar.flac, <Canción>_bass.flac, <Canción>.json (manifiesto)
        │  scripts/run_song.py <Canción> --separador roformer   (entorno .venv)
        ▼
outputs/<fecha>_<hora>_<canción>_roformer/   (+ separacion_roformer.json, evaluacion_melodia.json)
```

- **Entorno aparte (`.venv-rof`).** audio-separator necesita torch ≥ 2.3 y numpy ≥ 2. PyTorch dejó de publicar
  ruedas pip para macOS Intel después de 2.2.2, así que torch viene de conda-forge (que sí publica `osx-64`), y
  numpy 2 no convive con el `numpy==1.26.4` del entorno principal.
  Por la misma razón, las dependencias compiladas también vienen de conda-forge: torchvision (que pide `onnx2torch`;
  en PyPI, para Mac Intel, solo llega a la 0.17.2, que exige torch 2.2), y numba/llvmlite (que pide librosa; pip
  intenta compilar llvmlite y falla sin LLVM), además de librosa, onnxruntime, soundfile, scipy y resampy. Después,
  pip solo instala audio-separator y sus dependencias de Python puro.
- **librosa < 1.** audio-separator pide `librosa>=0.10` sin límite superior, pero importa `audioread`, que librosa 1.0
  ya no instala. Se fija `librosa=0.11` (con `<1`, conda elige la preliminar 1.0.0rc0) y se añade `audioread`.
- **CPU, no MPS.** En un Mac Intel con GPU AMD, torch ofrece MPS, pero audio-separator solo lo usa en procesadores
  ARM; aquí separa en CPU. El manifiesto guarda el dispositivo que usó de verdad (`entorno.dispositivo_usado`).
- **Pistas fuera de la carpeta de audios.** `pistas_roformer/` está fuera de `Angine de Poitrine Audios/` para que
  el flujo de Demucs (que busca `<Canción>_guitar.*` junto a la canción) nunca las tome sin querer. Solo se usan con
  `--separador roformer`. La carpeta está en `.gitignore`.
- **Corridas distinguibles.** Con `--separador roformer`, la carpeta de la corrida lleva la etiqueta `roformer`,
  `resumen.json` guarda `pistas.separador = "bs-roformer-sw"` con el SHA-256 del modelo, los parámetros y las
  versiones, y la corrida incluye una copia del manifiesto (`separacion_roformer.json`).

## Parámetros fijados

| Parámetro | Valor | Por qué |
|---|---|---|
| audio-separator | 0.48.0 | el overlap por defecto cambió en 0.47.0 |
| Entrada | ffmpeg a 44.1 kHz estéreo `pcm_f32le` | el remuestreo no depende de la herramienta |
| overlap | 2 | el de las métricas de MVSEP |
| segment_size / batch_size | 256 / 1 | por defecto; batch 1 para la memoria |
| Precisión / dispositivo | fp32 / CPU | en Mac Intel no hay MPS; sin autocast ni fp16 |
| Hilos de torch | 8, fijos | el número de hilos puede alterar el orden de las sumas |
| Semilla / algoritmos | `torch.manual_seed(0)`, `use_deterministic_algorithms(True, warn_only=True)` | |
| Salida | FLAC (no MP3) | el MP3 añade artefactos justo en los parciales que se transcriben |
| `pitch_shift` | 0 | nunca para análisis de afinación |

No se usa `--chunk_duration` (concatena trozos sin fundido) ni TTA. El YAML de audio-separator usa `dim_t: 801`
(el de MSST, 1101): el manifiesto guarda el `dim_t` y el SHA-256 del YAML que se usó.

## Instalación (Mac Intel)

```bash
# Miniforge (conda-forge), sin tocar el perfil de la terminal
curl -L -o ~/Downloads/Miniforge3.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh
bash ~/Downloads/Miniforge3.sh -b -p ~/miniforge3
make roformer-entorno      # crea .venv-rof con python 3.12, pytorch, ffmpeg y las dependencias compiladas de conda-forge, y audio-separator 0.48.0
```

En Apple Silicon basta un venv con `pip install "audio-separator[cpu]==0.48.0"`.

## Uso

```bash
.venv-rof/bin/python scripts/separar_roformer.py Sarniezz --fragmento 20 --comprobar-determinismo   # prueba de 20 s
make separar-roformer CANCION=Sarniezz     # canción completa → pistas_roformer/
make run-roformer CANCION=Sarniezz         # cuaderno con esas pistas → outputs/…_roformer/
.venv/bin/python scripts/evaluar_melodia.py <corrida_demucs> <corrida_roformer>
```

El checkpoint se guarda en `~/models/audio-separator` (fuera del repositorio; conviene conservar una copia porque
la cuenta original ya desapareció una vez).

## Resultados

Prueba con Sarniezz (275.7 s de audio) en un Mac Intel i9 de 8 núcleos con 16 GB.

### Funcionamiento

| | Resultado |
|---|---|
| Checkpoint | SHA-256 coincide con `BS-Rofo-SW-Fixed` |
| YAML | `dim_t` 801, `num_overlap` 2, `chunk_size` 588800 (SHA-256 `b558996f…`) |
| Dispositivo | CPU, fp32, 8 hilos |
| Determinismo (fragmento de 20 s, dos separaciones) | idénticas bit a bit (diferencia máxima 0) |
| Carga del modelo | 12.6 s (la primera vez, con descarga, ~86 s) |
| Separación de la canción completa | 3616 s (~60 min), **13.1 × tiempo real** |
| Cuaderno sobre las pistas | 183.6 s, igual que con Demucs |

Versiones: audio-separator 0.48.0, torch 2.14.1, numpy 2.5.5, onnxruntime 1.22.2, librosa 0.11.0, ffmpeg 9.0.2.

### Comparación con Demucs

Las dos corridas usan la misma versión del cuaderno y los mismos ajustes; solo cambian las pistas. La línea base usa
las pistas de `htdemucs_6s` que ya estaban junto a la canción. Valores en % de acierto contra la partitura
corregida (`evaluar_melodia.py --secciones`):

| | Demucs | RoFormer SW |
|---|---|---|
| Voz principal | 44.9 | 44.9 |
| Voz principal, sin contar octavas | 51.1 | 51.8 |
| Nota más aguda | 35.3 | 30.9 |
| Bajo | 78.6 | 76.5 |
| Tiempo medible | 83 % | 83 % |

Por sección (voz principal):

| Sección | n | Demucs | RoFormer SW |
|---|---|---|---|
| Riff del bajo (c. 9-13) | 2 | 28.6 | 28.6 |
| Riff, puente (c. 14) | 9 | 35.3 | 33.3 |
| Riff en bajo y guitarra 2 (c. 15-18) | 96 | 82.2 | 84.1 |
| Riff + acorde de la guitarra 1 (c. 19-22) | 96 | 81.8 | 83.1 |
| Frase 1 de la guitarra 1 sobre el riff (c. 23-26) | 86 | 12.4 | 7.5 |
| Frase 1 con bajo suelto (c. 27-30) | 160 | 55.9 | 40.3 |
| Frase 1 en 4/4 (c. 31-36) | 80 | 62.4 | 60.5 |
| Frase 1 con la guitarra 2 una octava abajo (c. 37-42) | 160 | 7.6 | 10.9 |
| Frase 1 + frase 2 aguda de la guitarra 2 (c. 43-51) | 164 | 19.3 | **43.0** |
| Patrón del bajo en guitarra 1 (c. 64-69) | 192 | 59.5 | 54.6 |
| Final libre de la guitarra 1 (c. 77-82) | 24 | 45.3 | 40.0 |

### Lectura

- **En conjunto, empate.** La voz principal queda igual (44.9) y las demás medidas se mueven 1-4 puntos en
  direcciones opuestas. El SDR más alto de MVSEP no se traduce en mejor transcripción sobre este material.
- **Donde ayuda:** las secciones de riff con las dos guitarras (c. 15-22, +1-2 puntos) y, sobre todo, la sección con
  la frase aguda de la guitarra 2 (c. 43-51), que pasa de 19.3 a 43.0. Ahí la nota más aguda baja (19.2 → 11.5):
  RoFormer deja más presente la frase 1 y la voz principal la sigue.
- **Donde empeora:** las secciones donde la guitarra 1 toca sola sobre el bajo (c. 23-30, c. 64-69 y el final).
  La mayor pérdida es la frase 1 con bajo suelto (55.9 → 40.3); el bajo también baja 2 puntos. Es compatible con
  que RoFormer reparta de otra forma la energía entre las pistas `guitar` y `bass` cuando los registros se cruzan.
- **Costo:** una hora de CPU por canción frente a unos minutos de Demucs en esta máquina.

**Decisión:** Demucs `htdemucs_6s` sigue siendo el separador por defecto. RoFormer SW queda integrado como opción
(`--separador roformer`) para estudiar secciones concretas como c. 43-51, y para repetir la comparación en otras
canciones o en una máquina con GPU. Una sola canción no basta para generalizar.
