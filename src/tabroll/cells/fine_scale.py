"""**`fine_scale`**: Crea una escala de dibujo con 24 filas por octava para que cada cuarto de tono tenga su propia casilla. `D_{1/4}` es un cuarto de tono por encima de D. Los acordes se siguen nombrando con la escala normal.
"""

def fine_scale(sc, tonic_midi):
    chromatic = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']
    steps = [50.0 * k for k in range(24)]
    names, degrees, colors = [], [], []

    for k, c in enumerate(steps):
        row = sc.row(c)
        low, t = int(math.floor(row)), row - math.floor(row)

        if t < 1e-9:                                                     # grado de la escala
            names.append(sc.names[low]); degrees.append(str(low + 1)); colors.append(sc.colors[low])
        else:                                                            # semitono o cuarto de tono fuera de la escala
            names.append(chromatic[(tonic_midi + k // 2) % 12] + ('_{1/4}' if k % 2 else ''))
            degrees.append(''); colors.append(mix(sc.colors[low], sc.colors[(low + 1) % sc.n], t))

    return Scale(steps, names=names, degrees=degrees, colors=colors, tonic_name=sc.tonic_name, tonic_octave=sc.tonic_octave, accidental_unit=50.0, tol=20.0)
