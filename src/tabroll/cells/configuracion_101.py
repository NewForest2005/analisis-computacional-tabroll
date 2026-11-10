"""Armonía de la canción: una fila por compás (`armonia`) y el resumen para el círculo (`armonia_resumen`). `run_song.py` los guarda en `armonia.json`.
"""

tonic_pc24 = (2 * tonic_pc) % 24                                               # la tónica del cuaderno (12 clases) en la rejilla de 24
armonia = harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24)
armonia_resumen = harmony_summary(armonia, tonic_pc24)

grados = sorted(armonia_resumen['fundamentales_por_grado'].items(), key=lambda kv: -kv[1])[:5]
print(f"Armonía: {len(armonia)} compases | confiable el {armonia_resumen['tiempo_confiable']:.0f}% del tiempo | "
      "fundamentales más usadas: " + ', '.join(f'{g} {100 * v:.0f}%' for g, v in grados if v > 0))
