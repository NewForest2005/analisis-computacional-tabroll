"""Ajustes de inicializacion:
"""

KEY_OVERRIDE = None
FINE_ROWS = True
TEMPO_OVERRIDE = None
BAR_LENGTHS = (2, 3, 4, 5, 6, 7, 8)
FORCE_BAR_BEATS = None
BEAT_DIV = 1
GRID = 0.25
MICRO_STEP = 50
NFFT_P, HOP_P = 4096, 512

TARGET_SR = 22050

HAS_DRUMS = True                                                                # False si el audio no trae batería
y_st, sr = librosa.load(audio_path, sr=TARGET_SR, mono=False)
y = y_st.mean(axis=0) if y_st.ndim > 1 else y_st

print(f'Duracion: {len(y)/sr:.1f} s | {sr} Hz')
