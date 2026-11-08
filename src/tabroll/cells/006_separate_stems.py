"""Celda 8 del notebook original. Descripcion asociada: separate_stems: separa la canción con la red neuronal Demucs (modelo htdemucs_6s, el que tiene pista de guitarra) y guarda la guitarra y el bajo como Canción_guitar.mp3 y Canción_bass.mp3 junto a la canción. La primera vez instala demucs-infer y descarga el modelo..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def separate_stems(audio, kinds=('guitar', 'bass'), model_name='htdemucs_6s'):
    if importlib.util.find_spec('demucs_infer') is None:
        subprocess.run([sys.executable, '-m', 'pip', '-q', 'install', 'demucs-infer'], check=True)

    import torch
    from demucs_infer.pretrained import get_model
    from demucs_infer.apply import apply_model
    from demucs_infer.audio import AudioFile

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Separando {audio.name} con {model_name} ({device})' + ('' if device == 'cuda' else '; sin GPU tarda varios minutos'))

    model = get_model(model_name); model.eval()
    wav = AudioFile(str(audio)).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()                                                   # la misma normalización que usa Demucs

    with torch.no_grad():
        out = apply_model(model, wav[None], device=device)[0].cpu()
    out = out * ref.std() + ref.mean()

    paths = {}
    for kind in kinds:
        x = np.ascontiguousarray(out[model.sources.index(kind)].numpy().T, dtype=np.float32)       # (muestras, canales)
        paths[kind] = audio.with_name(f'{audio.stem}_{kind}.mp3')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(model.samplerate), '-ac', str(x.shape[1]),
                        '-i', '-', '-b:a', '192k', str(paths[kind])], input=x.tobytes(), check=True)

    return paths
