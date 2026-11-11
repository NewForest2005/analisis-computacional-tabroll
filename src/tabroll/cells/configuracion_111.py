"""Círculo armónico de la canción (`circulo`) y su figura `circulo_armonico.png` en la carpeta de imágenes. `run_song.py` guarda el círculo en `circulo.json`.
"""

circulo = harmony_circle(armonia, tonic_pc24)
circulo.update(cancion=audio_path.stem, centro=PC24_NAMES[tonic_pc24], modo=armonia_resumen['modo']['nombre'])
ruta_circulo = draw_harmony_circle(circulo, OUTPUT_DIR / 'circulo_armonico.png')
fuertes = sorted(zip(circulo['posiciones'], circulo['fundamentales']), key=lambda kv: -kv[1])[:4]
print(f"Círculo armónico: {ruta_circulo.name} | fundamentales: " + ', '.join(f'{g} {100 * v:.0f}%' for g, v in fuertes if v > 0) +
      f" | {circulo['cambios']} cambios | {circulo['ciclos_distintos']} ciclos distintos"
      f" | {circulo['tiempo_sin_ciclo']:.0f}% del tiempo fuera de ciclos")
