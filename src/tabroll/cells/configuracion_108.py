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
armonia = chord_roles(armonia, tonic_pc24)                                   # cifrado, función, inversión y voz aguda
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

armonia_resumen['funciones'] = roles_summary(armonia)
fx = armonia_resumen['funciones']
print('         funciones: ' + ', '.join(f'{k} {v:.0f}%' for k, v in fx['funciones'].items()) +
      f" | voz aguda dentro del acorde: {fx['aguda_en_acorde']}%")
print('         inversiones: ' + ', '.join(f'{k} {v:.0f}%' for k, v in fx['inversiones'].items()))
print('         cifrados: ' + ', '.join(f'{k} {v:.0f}%' for k, v in list(fx['cifrados'].items())[:6]))

modo_menor = '♭3' in [x.strip() for x in armonia_resumen['modo']['nombre'].split(',')]
armonia, armonia_resumen['progresiones'] = chord_progressions(armonia, menor=modo_menor)
print('         grados: ' + ', '.join(f'{k} {v:.0f}%' for k, v in list(fx['nombres_grado'].items())[:5]))
print('         ejes de Lendvai: ' + ', '.join(f'{k} {v:.0f}%' for k, v in fx['ejes'].items()))
for clave, titulo in (('confiables', 'compases confiables'), ('todos', 'todos los compases')):
    pr = armonia_resumen['progresiones'][clave]
    print(f"         progresiones, {titulo} ({pr['compases']}): {pr['cambios']} cambios, {pr['por_quintas']:.0f}% por quintas | "
          'tabla de Piston: ' + ', '.join(f'{k} {v:.0f}%' for k, v in pr['uso_piston'].items()))
    print('           por ejes: ' + ', '.join(f'{k} {v:.0f}%' for k, v in pr['ejes'].items()) + ' | pasos: ' +
          ', '.join(f'{k} ×{v}' for k, v in pr['pasos_de_eje'].items()))
    print('           más frecuentes: ' + ', '.join(f'{p} ×{n}' for p, n in pr['frecuentes'][:5]))
    nombradas = [f"{k} ×{v['veces']}" for k, v in pr['con_nombre'].items()] + [f'vaivén {k} ×{v}' for k, v in pr['vaivenes'].items()]
    if nombradas:
        print('           con nombre: ' + ', '.join(nombradas))
