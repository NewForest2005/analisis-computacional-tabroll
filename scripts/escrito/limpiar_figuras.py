"""Versiones de las figuras del escrito sin títulos, subtítulos, notas ni claves de color.

Esos textos pasan a las leyendas del documento (docs/escrito/capitulos/*.tex). Lee las imágenes de
presentacion/img/ y docs/escrito/figuras/ y escribe docs/escrito/figuras/limpias/, que el escrito usa primero.
Uso: python scripts/escrito/limpiar_figuras.py [nombre.png ...]   (sin argumentos, todas)
"""
import os,sys,numpy as np
from PIL import Image
OUT="docs/escrito/figuras/limpias"; os.makedirs(OUT,exist_ok=True)
def path(n):
    for d in ("presentacion/img","docs/escrito/figuras"):
        if os.path.exists(f"{d}/{n}"): return f"{d}/{n}"
def bgcol(a): return np.median(np.concatenate([a[0],a[-1],a[:,0],a[:,-1]]),axis=0).astype(int)
def inkmask(a,bg): return (np.abs(a.astype(int)-bg).sum(2)>40)
def bands(a,gap=None):
    gap=gap or max(8,a.shape[0]//150)
    m=inkmask(a,bgcol(a)).any(1); out=[];s=None;last=-10**9
    for y,v in enumerate(m):
        if v:
            if s is None: s=y
            elif y-last>gap: out.append((s,last)); s=y
            last=y
    if s is not None: out.append((s,last))
    return out
def autocrop(a,pad=24):
    m=inkmask(a,bgcol(a)); ys=np.where(m.any(1))[0]; xs=np.where(m.any(0))[0]
    return a[max(ys[0]-pad,0):ys[-1]+pad+1, max(xs[0]-pad,0):xs[-1]+pad+1]
def proc(n, drop=(), drop_last=0, rects=(), xmax=None, xmin=None, top_lines=0, gap=None, keep_crop=True):
    a=np.array(Image.open(path(n)).convert("RGB")); bg=bgcol(a); H,W=a.shape[:2]
    b=bands(a,gap)
    dl=[b[i] for i in drop]+(b[-drop_last:] if drop_last else [])
    for r in rects:   # fracciones (x0,y0,x1,y1) o píxeles si >1
        x0,y0,x1,y1=[int(v*(W if i%2==0 else H)) if v<=1 else int(v) for i,v in enumerate(r)]
        a[y0:y1,x0:x1]=bg
    if top_lines:     # quita las primeras líneas de texto con rejilla fina
        fb=bands(a,6); dl+=fb[:top_lines]
    keep=np.ones(H,bool)
    for y0,y1 in dl: keep[y0:y1+1]=False
    a=a[keep]
    if xmax: a=a[:, : int(xmax*W) if xmax<=1 else int(xmax)]
    if xmin: a=a[:, int(xmin*W) if xmin<=1 else int(xmin):]
    if keep_crop: a=autocrop(a)
    Image.fromarray(a.astype(np.uint8)).save(f"{OUT}/{n}")
    return a.shape
def tarjeta(n):
    a=np.array(Image.open(path(n)).convert("RGB")); H,W=a.shape[:2]
    card=a[H//2,W//2].astype(int)  # fondo de la tarjeta
    m=(np.abs(a[:, int(W*.1):int(W*.9)].astype(int)-card).sum(2)>60).any(1)
    # filas de texto dentro de la tarjeta (entre y=40 y H-40)
    rows=[];s=None;last=-99
    for y in range(40,H-40):
        if m[y]:
            if s is None: s=y
            elif y-last>8: rows.append((s,last)); s=y
            last=y
    rows.append((s,last))
    # primera fila = encabezado; dos últimas = pie
    keep=np.ones(H,bool)
    keep[rows[0][0]-6:rows[2][0]-30]=False      # encabezado y su raya
    keep[rows[-2][0]-6:rows[-1][1]+8]=False     # pie
    out=autocrop(a[keep])
    Image.fromarray(out).save(f"{OUT}/{n}"); return rows[0],rows[-2:]
SONGS=["mata_zyklek","fabienk","sarniezz","yor_zarad","utzp","angor"]
spec={
 "formula_js.png":dict(drop=[0]), "formula_percentil.png":dict(drop=[0]),
 "acierto_herramienta.png":dict(drop=[3,4]),
 "1a_armonia_matriz_verosimilitud.png":dict(drop=[0]),
 "1b_armonia_mapa_fundamentales.png":dict(drop=[0],xmax=0.62),
 "2a_melodia_uso_cuartos_de_tono.png":dict(drop=[0]),
 "2b_melodia_circulo_24edo.png":dict(drop=[0]),
 "3a_sintesis_ciclos_metricos.png":dict(drop=[0]),
 "3c_sintesis_corpus_por_bloque.png":dict(drop=[0,1]),
 "g_campos_tiempo.png":dict(drop=[0,15,16,17]),
 "g_campos_resumen.png":dict(drop=[0,1]),
 "g_ciclos_metricos.png":dict(drop=[0,1,2,13]),
 "g_radar_ritmico.png":dict(drop=[0,1,9],rects=[(2,300,560,630)]),
 "bucle_compas.png":dict(drop=[0,1,10,11,12]),
 "g_clasificacion_detalle.png":dict(drop=[0,4,5,6]),
 "g_equivalencias_edo.png":dict(drop=[0,1,4]),
 "g_matriz_rock_pop.png":dict(drop=[0]),
 "g_perfil.png":dict(drop=[0,1,4,7,10,13,16,17,18]),
 "g_tarjetas_1.png":dict(drop=[0,1,2]),
 "g_tarjetas_2.png":dict(drop=[3]),
 "g_verosimilitud_matriz.png":dict(drop=[0,1,3]),
 "g_verosimilitud_mapa.png":dict(drop=[0,1,5],xmax=0.715),
 "g_distancias_estilos.png":dict(top_lines=1,rects=[(1480,5060,1873,5190)]),
 "g_veredictos_estilos_1.png":dict(drop=[0,1,2]),
 "g_veredictos_estilos_2.png":dict(drop_last=1),
 "g_microtonal_uso.png":dict(top_lines=1,rects=[(1550,4440,1974,4525)]),
 "g_microtonal_escalas_1.png":dict(drop=[0,1,2]),
 "g_bloques.png":dict(drop=[0,1,3,4,5]),  # la fila n= se monta con el rótulo del eje
 "g_bloques_sintesis.png":dict(drop=[0,1,2,3,4]),
}
for g in ("kg","zappa","kc","gg"): spec[f"g_comparar_{g}.png"]=dict(drop=[0,5])
for s in ["mata_zyklek","fabienk","sarniezz","yor_zarad","utzp"]: spec[f"{s}_radar_estilos.png"]=dict(drop=[0,1,5])
for s in SONGS:
    spec[f"{s}_tira_de_ciclos.png"]=dict(drop=[0,1])
    spec[f"{s}_circulo_armonico.png"]=dict(drop=[0],drop_last=1,rects=[(-320,0,0,0)])  # se ajusta abajo
spec["sarniezz_mapa_ciclos.png"]=dict(drop=[0])
only=sys.argv[1:]
for n,kw in spec.items():
    if only and n not in only: continue
    if n.endswith("circulo_armonico.png"):
        a=Image.open(path(n)); W=a.width; b=bands(np.array(a.convert("RGB")))
        arr=np.array(a.convert("RGB")).astype(int); y0,y1=b[1][0]-4,b[2][1]+4
        # la clave empieza en la muestra azul de «Fundamentales», en la mitad derecha
        blue=(np.abs(arr[y0:y1,W//2:]-[44,120,215]).sum(2)<60).any(0)
        x0=W//2+int(np.argmax(blue))-6 if blue.any() else W-315
        kw=dict(drop=[0],drop_last=1,rects=[(540,55,840,142)] if n.startswith("sarniezz") else [(x0,y0,W,y1)])
    print(n, proc(n,**kw))
for s in SONGS:
    if not only or f"{s}_tarjeta.png" in only: print(s, tarjeta(f"{s}_tarjeta.png"))

def partir(n):
    """Parte una figura alta en dos mitades (…_a, …_b) por el hueco entre filas más cercano a la mitad,
    para ponerlas lado a lado en el escrito."""
    a=np.array(Image.open(f"{OUT}/{n}").convert("RGB")); H,W=a.shape[:2]
    ink=inkmask(a,bgcol(a))
    fijas=ink[H//3:2*H//3].mean(0)>0.9      # rejilla y franjas verticales: se ignoran
    m=ink[:,~fijas].any(1)
    # tramos en blanco; se corta en el centro de uno de los más largos (entre grupos, no dentro de un grupo)
    tramos=[];s=None
    for y in range(H//3,2*H//3):
        if not m[y] and s is None: s=y
        if m[y] and s is not None: tramos.append((s,y)); s=None
    largo=max(b-a for a,b in tramos)
    y=min(((a+b)//2 for a,b in tramos if b-a>=0.8*largo),key=lambda v:abs(v-H//2))
    base=n[:-4]
    for suf,parte in (("a",a[:y]),("b",a[y:])):
        Image.fromarray(autocrop(parte).astype(np.uint8)).save(f"{OUT}/{base}_{suf}.png")
    return y
for n in ("g_distancias_estilos.png","g_microtonal_uso.png"):
    if not only or n in only: print(n,"partida en y =",partir(n))
