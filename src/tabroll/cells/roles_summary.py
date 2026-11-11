"""**`roles_summary`**: Reparto del tiempo de los compases confiables por función (familia y con su calidad), nombre y clase del grado, inversión, cifrado, papel de la voz aguda y eje de Lendvai (en %, de mayor a menor), y qué parte de la voz aguda cae dentro del acorde, ponderada por la duración de cada compás.
"""

def roles_summary(armonia, min_conf=0.5):
    ok = [r for r in armonia if r.get('funcion') and (r.get('confianza') or 0) >= min_conf]
    dur = lambda r: r['fin_s'] - r['inicio_s']
    total = sum(dur(r) for r in ok) or 1.0

    def share(key):
        acc = {}
        for r in ok:
            if r.get(key) is not None:
                acc[r[key]] = acc.get(r[key], 0.0) + dur(r)
        return {k: round(100.0 * v / total, 1) for k, v in sorted(acc.items(), key=lambda kv: -kv[1])}

    en = [(r['aguda_en_acorde'], dur(r)) for r in ok if r.get('aguda_en_acorde') is not None]
    peso = sum(w for _, w in en)
    return dict(funciones=share('funcion'), funciones_detalle=share('funcion_texto'), nombres_grado=share('nombre_grado'),
                clases_grado=share('clase_grado'), inversiones=share('inversion'), cifrados=share('cifrado'),
                papeles_aguda=share('papel_aguda'), ejes=share('eje'),
                aguda_en_acorde=round(sum(a * w for a, w in en) / peso, 1) if peso else None,
                compases_confiables=len(ok))
