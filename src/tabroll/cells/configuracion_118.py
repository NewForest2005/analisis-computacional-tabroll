"""Patrones de ciclo de la canción: agrega a cada compás cuánto se acoge al patrón y por qué, y el resumen a `armonia_resumen['patrones']`.
"""

armonia, armonia_resumen['patrones'] = cycle_patterns(armonia, cycles, {'Voz aguda': raw_high, 'Voz grave': raw_bass},
                                                     lens, tonic_pc24)
for voz, pats in armonia_resumen['patrones'].items():
    print(f'Patrones de ciclo, {voz.lower()}:')
    for letra, d in pats.items():
        variacion = ', '.join(f'{c} ×{v}' for c, v in d['variacion'][:3])
        print(f"  {letra} ({d['periodo_s']:.2f} s, {d['vueltas']} vueltas, {d['notas']} notas, sobre {d['acorde_usual']}): se acoge "
              f"{d['acoge']:.0f}%, iguales {d['iguales']:.0f}% | motivos: " +
              ', '.join(f'{k} {v:.0f}%' for k, v in d['motivos'].items() if k != 'igual al patrón'))
        print(f"     patrón: {' · '.join(d['patron'].split(' · ')[:8])}{' …' if d['notas'] > 8 else ''}")
        res = f"{d['resuelven']:.0f}% de {d['disonantes']} disonantes resuelven por grado" if d['disonantes'] else 'sin disonantes'
        print(f"     {res}; termina en {d['termina']} ({d['cierra']})" + (f' | dónde varía: {variacion}' if variacion else ''))
