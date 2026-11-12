"""Notas columna de la canción: agrega las columnas a cada compás de `armonia` y su resumen a `armonia_resumen['columnas']`; `run_song.py` las guarda en `armonia.json` y en `armonia_por_compas.csv`.
"""

armonia = melodic_columns(armonia, raw_bass, raw_high, lens)
armonia_resumen['columnas'] = columns_summary(armonia)
cs = armonia_resumen['columnas']
print(f"Columnas ({cs['compases']} compases confiables): la nota principal es " +
      ', '.join(f'{k} {v:.0f}%' for k, v in cs['papeles'].items()) + f" | dentro del acorde {cs['en_acorde']:.0f}% | "
      'en el pulso ' + ', '.join(f'{k}: {v:.0f}%' for k, v in list(cs['pulsos'].items())[:3]))
print('          intervalo con el bajo: ' + ', '.join(f'{k} {v:.0f}%' for k, v in cs['intervalos'].items()) +
      ' | arcos: ' + ', '.join(f'{k} {v:.0f}%' for k, v in cs['arcos'].items()))
if cs['por_ciclo']:
    print('          por ciclo de la voz aguda: ' + '; '.join(
        f"{c}: {d['columna']} ×{d['veces']}/{d['compases']}, {d['arco']}" for c, d in cs['por_ciclo'].items()))
