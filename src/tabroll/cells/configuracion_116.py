"""Figuras melódicas de la canción: agrega los giros y las notas extrañas a cada compás de `armonia` y el resumen a `armonia_resumen['melodia']`.
"""

armonia, armonia_resumen['melodia'] = melodic_figures(armonia, raw_high, lens, tonic_pc24)
ml = armonia_resumen['melodia']
top = lambda d, n=6: ', '.join(f'{k} {v:.0f}%' for k, v in list(d.items())[:n])
print(f"Melodía ({ml['notas']} notas de la voz aguda): grado conjunto {ml['grado_conjunto']:.0f}%, saltos {ml['saltos']:.0f}%, "
      f"notas repetidas {ml['repetidas']:.0f}%, intervalos microtonales {ml['microtonales']:.0f}% | sube {ml['sube']:.0f}%, baja {ml['baja']:.0f}%")
print('          intervalos: ' + top(ml['intervalos'], 8))
print('          giros: ' + top(ml['giros']))
print(f"          espectro: {top(ml['espectro'], 8)} | en grados de cuarto de tono {ml['espectro_microtonal']:.0f}%")
print(f"          notas extrañas: {ml['extranas']:.0f}% de {ml['notas_en_confiables']} notas en compases confiables | " + top(ml['tipos_extranas']))
if ml['por_ciclo']:
    print('          giro principal por ciclo de la voz aguda: ' + '; '.join(f"{c}: {d['giro']} {d['parte']:.0f}%" for c, d in ml['por_ciclo'].items()))
