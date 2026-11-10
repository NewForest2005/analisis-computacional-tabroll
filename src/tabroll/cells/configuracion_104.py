"""Armonía de la canción: centro y modo en 24-EDO, una fila por compás (`armonia`) y el resumen con las capas del círculo (`armonia_resumen`). `CENTRO` permite fijar el centro a mano para comparar. `run_song.py` lo guarda todo en `armonia.json`.
"""

CENTRO = 'cuaderno'   # 'cuaderno': la tónica de la celda de tonalidad (coincide con el oído en las 5 canciones) | 'auto': medida de centro en 24-EDO | o una nota: 'E', 'D+', ...

centro24 = center24_by_layer(raw_bass, raw_high, cycles)
tonica_cuaderno_pc24 = (2 * tonic_pc) % 24
if CENTRO == 'auto':
    tonic_pc24 = centro24['centro_pc24']
elif CENTRO == 'cuaderno':
    tonic_pc24 = tonica_cuaderno_pc24
else:
    tonic_pc24 = PC24_NAMES.index(CENTRO)

armonia = harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24)
armonia_resumen = harmony_summary(armonia, tonic_pc24)
armonia_resumen.update(
    centro=PC24_NAMES[tonic_pc24], regla_centro=CENTRO,
    centro_24edo=PC24_NAMES[centro24['centro_pc24']], margen_centro=centro24['margen'],
    centro_bajo=PC24_NAMES[centro24['centro_bajo_pc24']], centro_aguda=PC24_NAMES[centro24['centro_aguda_pc24']],
    tonica_cuaderno=PC24_NAMES[tonica_cuaderno_pc24],
    modo=mode24(armonia, tonic_pc24), capas=harmony_layers(armonia, tonic_pc24),
    ciclos={voz: [dict(start=round(float(c.start), 3), end=round(float(c.end), 3), period=round(float(c.period), 4),
                       label=getattr(c, 'label', None)) for c in cs] for voz, cs in cycles.items()})   # para medir con los mismos ciclos

capas = armonia_resumen['capas']
grados = sorted(armonia_resumen['fundamentales_por_grado'].items(), key=lambda kv: -kv[1])[:5]
print(f"Armonía: centro {armonia_resumen['centro']} (bajo {armonia_resumen['centro_bajo']}, voz aguda {armonia_resumen['centro_aguda']}, "
      f"tónica de 12 clases {armonia_resumen['tonica_cuaderno']}) | modo {armonia_resumen['modo']['nombre']}")
print(f"         {len(armonia)} compases | confiable el {armonia_resumen['tiempo_confiable']:.0f}% del tiempo | "
      "fundamentales: " + ', '.join(f'{g} {100 * v:.0f}%' for g, v in grados if v > 0))
print(f"         movimientos: " + ', '.join(f'{k} {100 * v:.0f}%' for k, v in capas['movimientos'].items()) +
      f" | cambios por compás {capas['cambios_por_compas']:.2f}")
