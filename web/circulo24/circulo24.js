/* Círculo de 24 notas animado (Angine de Poitrine).
 *
 * Lee window.CIRCULO24 (lo escribe scripts/comparacion/exportar_circulo24.py en datos.js):
 *   { titulo, desde, hasta, tonica_pc24, tempo_bpm, audio, audios,
 *     voces: { aguda: [[inicio_s, fin_s, grado24], ...], grave: [...] } }
 * Los tiempos ya vienen relativos al inicio del fragmento. grado24: 0 = Do, 1 = Do + ¼ de tono, 2 = Do#, ... 23 = Si + ¼.
 *
 * Dibuja 12 círculos grandes con nombre (los semitonos) y 12 pequeños entre ellos (los cuartos de tono), con Do arriba
 * y en sentido horario, como en los videos de la banda. La nota que suena se pinta en rojo (voz aguda) o azul (grave);
 * las que acaban de sonar dejan una estela que se apaga en ESTELA_S segundos. La «huella» es una barra por grado,
 * por fuera del círculo, con el tiempo acumulado en cada uno hasta el instante actual: se ve cómo se arma la escala.
 * Si hay audio, el tiempo lo manda el audio; si no, un reloj propio.
 */
(function () {
  "use strict";
  const D = window.CIRCULO24;
  if (!D) {
    document.body.insertAdjacentHTML("beforeend", "<p>No se encontró datos.js. Corre antes scripts/comparacion/exportar_circulo24.py.</p>");
    return;
  }

  const NOMBRES = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"];
  const COLOR = { aguda: "#e5322d", grave: "#2a78d6" };
  const ESTELA_S = 1.2;
  const R = 230;                       // radio del anillo de notas
  const R_HUELLA = 292;                // donde empiezan las barras de la huella
  const LARGO_HUELLA = 46;
  const SVGNS = "http://www.w3.org/2000/svg";
  const duracion = Math.max(0.01, D.hasta - D.desde);

  const nombre24 = (g) => NOMBRES[Math.floor(g / 2)] + (g % 2 ? " +¼" : "");
  const angulo = (g) => ((g * 15 - 90) * Math.PI) / 180;
  const el = (tag, attrs, padre) => {
    const e = document.createElementNS(SVGNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(e);
    return e;
  };

  // ───────────── dibujo fijo ─────────────
  const svg = el("svg", { viewBox: "-350 -350 700 700", role: "img", "aria-label": "Círculo de 24 notas" });
  document.getElementById("circulo").appendChild(svg);
  el("circle", { cx: 0, cy: 0, r: R, class: "fondo" }, svg);
  const centro = el("text", { x: 0, y: 40, class: "veinticuatro" }, svg);
  centro.textContent = "24";
  const etiqueta = el("text", { x: 0, y: 110, class: "etiqueta" }, svg);

  const nodos = [];
  const capaHuella = el("g", {}, svg);
  const capaAcorde = el("g", {}, svg);
  for (let g = 0; g < 24; g++) {
    const a = angulo(g);
    const x = R * Math.cos(a), y = R * Math.sin(a);
    const grande = g % 2 === 0;
    const grupo = el("g", { transform: `translate(${x.toFixed(1)},${y.toFixed(1)})` }, svg);
    const radio = grande ? 34 : 13;
    const base = el("circle", { r: radio, class: grande ? "nota" : "cuarto" }, grupo);
    const estela = el("circle", { r: radio, class: "estela", opacity: 0 }, grupo);
    const activo = el("circle", { r: radio, class: "activo", opacity: 0 }, grupo);
    let texto = null;
    if (grande) {
      texto = el("text", { y: 7, class: "nombre" }, grupo);
      texto.textContent = NOMBRES[g / 2];
    }
    if (D.tonica_pc24 !== null && D.tonica_pc24 !== undefined && ((D.tonica_pc24 % 24) + 24) % 24 === g) {
      el("circle", { r: radio + 8, class: "tonica" }, grupo);
    }
    const x1 = R_HUELLA * Math.cos(a), y1 = R_HUELLA * Math.sin(a);
    const barra = el("line", { x1: x1, y1: y1, x2: x1, y2: y1, class: "huella" }, capaHuella);
    nodos.push({ base, estela, activo, texto, barra, a });
  }

  // ───────────── controles ─────────────
  const $ = (id) => document.getElementById(id);
  const boton = $("reproducir"), barraT = $("tiempo"), rotulo = $("reloj"), selPista = $("pista"), selVoz = $("voz"),
    velocidad = $("velocidad"), chkHuella = $("ver-huella"), chkAcordes = $("ver-acordes");
  $("titulo").textContent = D.titulo;
  $("subtitulo").textContent = `${D.desde.toFixed(1)} s a ${D.hasta.toFixed(1)} s` + (D.tempo_bpm ? ` · ${Math.round(D.tempo_bpm)} BPM` : "") +
    (D.tonica_pc24 !== null && D.tonica_pc24 !== undefined ? ` · tónica ${nombre24(((D.tonica_pc24 % 24) + 24) % 24)}` : "");
  barraT.max = duracion;
  if (!D.voces.grave || !D.voces.grave.length) {
    for (const o of selVoz.options) if (o.value !== "aguda") o.disabled = true;
  }

  // Carga las pistas que exportó Python. `audio` conserva compatibilidad con exportaciones antiguas.
  const rutas = D.audios || (D.audio ? { mezcla: D.audio } : {});
  const elementos = {};
  for (const [nombre, ruta] of Object.entries(rutas)) {
    const a = document.createElement("audio");
    a.preload = "auto";
    a.src = ruta;
    elementos[nombre] = a;
    $("audios").appendChild(a);
  }
  const COMBINACIONES = {
    guitarra: ["guitarra"],
    bajo: ["bajo"],
    guitarra_bajo: ["guitarra", "bajo"],
    guitarra_bajo_bateria: ["guitarra", "bajo", "bateria"],
    mezcla: ["mezcla"],
  };
  const opciones = Object.keys(elementos);
  for (const o of selPista.options) {
    const necesita = COMBINACIONES[o.value] || [];
    o.disabled = !necesita.length || necesita.some((n) => !elementos[n]);
  }
  const disponible = (v) => (COMBINACIONES[v] || []).length > 0 && COMBINACIONES[v].every((n) => elementos[n]);
  const primera = ["guitarra_bajo", "guitarra", "bajo", "mezcla"].find(disponible);
  if (primera) selPista.value = primera;
  else selPista.disabled = true;
  const pistasActivas = () => (COMBINACIONES[selPista.value] || []).map((n) => elementos[n]).filter(Boolean);
  const usarAudio = () => pistasActivas().length > 0;
  const vozPorPista = {
    guitarra: "aguda",
    bajo: "grave",
    guitarra_bajo: "ambas",
    guitarra_bajo_bateria: "ambas",
    mezcla: "ambas",
  };
  let tPropio = 0, corriendo = false, ultimo = null;
  const ahora = () => {
    const activas = pistasActivas();
    return Math.max(0, usarAudio() ? activas[0].currentTime - D.desde : tPropio);
  };
  const irA = (t) => {
    t = Math.min(Math.max(0, t), duracion);
    for (const a of pistasActivas()) a.currentTime = D.desde + t;
    tPropio = t;
  };
  const reproducir = () => {
    if (ahora() >= duracion - 0.01) irA(0);
    corriendo = true;
    boton.textContent = "Pausa";
    if (usarAudio()) {
      for (const a of pistasActivas()) {
        a.playbackRate = parseFloat(velocidad.value);
        a.play().catch(() => {});
      }
    }
  };
  const pausar = () => {
    corriendo = false;
    boton.textContent = "Reproducir";
    for (const a of pistasActivas()) a.pause();
  };
  boton.addEventListener("click", () => (corriendo ? pausar() : reproducir()));
  barraT.addEventListener("input", () => irA(parseFloat(barraT.value)));
  velocidad.addEventListener("change", () => { for (const a of pistasActivas()) a.playbackRate = parseFloat(velocidad.value); });
  selPista.addEventListener("change", () => {
    const t = ahora();
    for (const a of Object.values(elementos)) a.pause();
    if (vozPorPista[selPista.value]) selVoz.value = vozPorPista[selPista.value];
    irA(t);
    document.title = `${D.titulo} · ${selPista.options[selPista.selectedIndex].textContent}`;
  });
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT") {
      e.preventDefault();
      corriendo ? pausar() : reproducir();
    }
  });
  for (const a of Object.values(elementos)) a.addEventListener("loadedmetadata", () => irA(ahora()));

  // ───────────── animación ─────────────
  const voces = () => (selVoz.value === "ambas" ? ["aguda", "grave"] : [selVoz.value]);
  const fmt = (s) => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`;

  function dibujarAcorde(grados) {
    while (capaAcorde.firstChild) capaAcorde.removeChild(capaAcorde.firstChild);
    if (!chkAcordes.checked || grados.length < 2) return;
    const puntos = grados.map((g) => {
      const a = angulo(g);
      return [R * Math.cos(a), R * Math.sin(a)];
    });
    if (puntos.length === 2) {
      el("line", { x1: puntos[0][0], y1: puntos[0][1], x2: puntos[1][0], y2: puntos[1][1], class: "acorde" }, capaAcorde);
    } else {
      const cadena = puntos.concat([puntos[0]]).map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
      el("polyline", { points: cadena, class: "acorde" }, capaAcorde);
    }
  }

  function cuadro(ts) {
    if (corriendo && !usarAudio) {
      if (ultimo !== null) tPropio += ((ts - ultimo) / 1000) * parseFloat(velocidad.value);
    }
    ultimo = ts;
    let t = ahora();
    if (t >= duracion) {
      t = duracion;
      if (corriendo) pausar();
    }
    barraT.value = t;
    rotulo.textContent = `${fmt(t)} / ${fmt(duracion)}`;

    const activo = new Array(24).fill(null);   // voz que suena en cada grado
    const estela = new Array(24).fill(0);
    const acumulado = new Array(24).fill(0);
    const sonando = [];
    const gradosAcorde = new Set();
    for (const v of voces()) {
      for (const [s, e, g] of D.voces[v] || []) {
        if (s > t) break;                       // las notas vienen ordenadas por inicio
        acumulado[g] += Math.min(e, t) - s;
        if (t < e) {
          if (!activo[g] || v === "aguda") activo[g] = v;
          sonando.push(nombre24(g));
          gradosAcorde.add(g);
        } else if (t - e < ESTELA_S) {
          estela[g] = Math.max(estela[g], 0.55 * (1 - (t - e) / ESTELA_S));
        }
      }
    }
    dibujarAcorde([...gradosAcorde].sort((a, b) => a - b));
    const maximo = Math.max(...acumulado, 1e-9);
    const verHuella = chkHuella.checked;
    for (let g = 0; g < 24; g++) {
      const n = nodos[g];
      const v = activo[g];
      n.activo.setAttribute("opacity", v ? 1 : 0);
      if (v) n.activo.setAttribute("fill", COLOR[v]);
      n.estela.setAttribute("opacity", v ? 0 : estela[g].toFixed(3));
      if (n.texto) n.texto.classList.toggle("encendido", !!v);
      const largo = verHuella ? (LARGO_HUELLA * acumulado[g]) / maximo : 0;
      n.barra.setAttribute("x2", ((R_HUELLA + largo) * Math.cos(n.a)).toFixed(1));
      n.barra.setAttribute("y2", ((R_HUELLA + largo) * Math.sin(n.a)).toFixed(1));
      n.barra.classList.toggle("es-cuarto", g % 2 === 1);
    }
    etiqueta.textContent = [...new Set(sonando)].join(" · ");
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(cuadro);
})();
