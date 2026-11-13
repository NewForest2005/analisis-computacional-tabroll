"""Centros por tramo de la canción: agrega el tramo y su centro a cada compás de `armonia` y el resumen a `armonia_resumen['centros_locales']`.
"""

armonia, armonia_resumen['centros_locales'] = local_centers(armonia, raw_bass, raw_high, cycles, tonic_pc24)
cl = armonia_resumen['centros_locales']
print(f"Centros por tramo (ciclos de la {cl['voz'].lower()}): el centro de la canción ocupa el {cl['centro_estable']:.0f}% | "
      f"{cl['modulaciones']} cambios de centro seguros, {cl['tramos_dudosos']} tramos dudosos")
for x in cl['tramos']:
    print(f"  {x['inicio']}–{x['fin']} {x['ciclo']:2s} centro {x['centro']}{'' if x['seguro'] else '?'} ({x['grado']}: "
          f"{x['respecto_del_centro']}) | modo {x['modo']} | margen {x['margen']:.2f}" +
          (f" | desde el anterior: {x['desde_el_anterior']}" if x['desde_el_anterior'] else ''))
