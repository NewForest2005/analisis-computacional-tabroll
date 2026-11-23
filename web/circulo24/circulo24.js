/* Círculo de 24 notas animado (Angine de Poitrine).
 *
 * Lee window.CIRCULO24 (lo escribe scripts/comparacion/exportar_circulo24.py en datos.js):
 *   { titulo, desde, hasta, audio_inicio, tonica_pc24, tempo_bpm, audio, audios,
 *     voces: { aguda: [[inicio_s, fin_s, grado24], ...], grave: [...] } }
 * Los tiempos de las notas vienen relativos al inicio del fragmento. grado24: 0 = Do, 1 = Do + ¼ de tono, 2 = Do#, ...
 * `audio_inicio` es el segundo del archivo de audio donde empieza el fragmento (0 si el audio ya viene recortado; si
 * falta, se usa `desde`).
 *
 * Dos disposiciones:
 * - cromática: los 24 grados en orden, Do arriba y en sentido horario, como en los videos de la banda; círculos grandes
 *   para los 12 regulares y pequeños para los cuartos de tono;
 * - quintas: los dos campos de 24-EDO (la quinta mide 14 pasos y mcd(14, 24) = 2), como en la gráfica 2b: el anillo
 *   exterior es el ciclo de quintas de los grados regulares y el interior el de los cuartos de tono; cada «+» queda
 *   junto a su vecino regular.
 * La nota que suena se pinta en rojo (voz aguda) o verde (grave); las que acaban de sonar dejan una estela que se apaga en
 * ESTELA_S segundos. La «huella» es una barra por grado con el tiempo acumulado hasta el instante actual: se ve cómo se
 * arma la escala. Si hay audio, el tiempo lo manda el audio; si no, un reloj propio.
 *
 * Parámetros de la dirección (opcionales): ?disposicion=quintas, ?voz=ambas, ?pista=guitarra.
 * Dentro de un iframe (la presentación) usa el tema claro, se pausa al recibir el mensaje «circulo24:pausar» y pasa las
 * flechas del teclado a la presentación.
 */
(function () {
  "use strict";
  const D = window.CIRCULO24;
  if (!D) {
    document.body.insertAdjacentHTML("beforeend", "<p>No se encontró datos.js. Corre antes scripts/comparacion/exportar_circulo24.py.</p>");
    return;
  }
  const embebido = window.self !== window.top;
  if (embebido) {
    document.documentElement.classList.add("embebido");
    document.documentElement.setAttribute("data-theme", "light");
  }
  const parametros = new URLSearchParams(location.search);
  const estilo = getComputedStyle(document.documentElement);
  const COLOR = { aguda: estilo.getPropertyValue("--aguda").trim(), grave: estilo.getPropertyValue("--grave").trim() };

  const NOMBRES = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"];
  const ESTELA_S = 1.2;
  const R = 230;                       // anillo de notas (cromática) y anillo exterior (quintas)
  const R_INTERNO = 150;               // anillo de los cuartos de tono en «quintas»
  const R_HUELLA = 292;                // donde empiezan las barras de la huella hacia afuera
  const LARGO_HUELLA = 46;
  const LARGO_INTERNO = 18;            // barras de los cuartos de tono en «quintas» (entre los dos anillos)
  const SVGNS = "http://www.w3.org/2000/svg";
  const duracion = Math.max(0.01, D.hasta - D.desde);
  const inicioAudio = D.audio_inicio ?? D.desde;
  const tonica = D.tonica_pc24 === null || D.tonica_pc24 === undefined ? null : ((D.tonica_pc24 % 24) + 24) % 24;

  const nombre24 = (g) => NOMBRES[Math.floor(g / 2)] + (g % 2 ? "+" : "");
  const el = (tag, attrs, padre) => {
    const e = document.createElementNS(SVGNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(e);
    return e;
  };

  // Posición de cada grado según la disposición
  function lugar(g, modo) {
    if (modo === "quintas") {
      const k = (7 * Math.floor(g / 2)) % 12;          // 7 es el inverso de 7 módulo 12: 14k ≡ g (mod 24)
      return { a: ((k * 30 - 90) * Math.PI) / 180, r: g % 2 ? R_INTERNO : R };
    }
    return { a: ((g * 15 - 90) * Math.PI) / 180, r: R };
  }
  const radioNodo = (g, modo) => (g % 2 === 0 ? 34 : modo === "quintas" ? 22 : 13);

  // ───────────── dibujo fijo ─────────────
  const svg = el("svg", { viewBox: "-350 -350 700 700", role: "img", "aria-label": "Círculo de 24 notas" });
  document.getElementById("circulo").appendChild(svg);
  el("circle", { cx: 0, cy: 0, r: R, class: "fondo" }, svg);
  const anilloExterior = el("circle", { cx: 0, cy: 0, r: R, class: "anillo", stroke: "var(--regular)" }, svg);
  const anilloInterior = el("circle", { cx: 0, cy: 0, r: R_INTERNO, class: "anillo", stroke: "var(--cuarto)" }, svg);
  const centro = el("text", { x: 0, y: 50, class: "veinticuatro" }, svg);
  centro.textContent = "24";
  const etiqueta = el("text", { x: 0, y: 12, class: "etiqueta" }, svg);

  const capaHuella = el("g", {}, svg);
  const capaAcorde = el("g", {}, svg);
  const nodos = [];
  for (let g = 0; g < 24; g++) {
    const grupo = el("g", { class: "g" }, svg);
    const regular = g % 2 === 0;
    const base = el("circle", { class: regular ? "nota" : "cuarto" }, grupo);
    const estela = el("circle", { class: "estela", opacity: 0 }, grupo);
    const activo = el("circle", { class: "activo", opacity: 0 }, grupo);
    const texto = el("text", { class: regular ? "nombre" : "nombre-cuarto" }, grupo);
    texto.textContent = regular ? NOMBRES[g / 2] : nombre24(g);
    const marca = g === tonica ? el("circle", { class: "tonica" }, grupo) : null;
    const barra = el("line", { class: "huella" + (regular ? "" : " es-cuarto") }, capaHuella);
    nodos.push({ g, grupo, base, estela, activo, texto, marca, barra, lugar: null });
  }

  function colocar(modo) {
    const quintas = modo === "quintas";
    // style (no el atributo): la hoja de estilos ya fija una opacidad y el atributo SVG quedaría debajo
    anilloExterior.style.opacity = quintas ? "" : 0;
    anilloInterior.style.opacity = quintas ? "" : 0;
    centro.style.opacity = quintas ? 0 : "";
    etiqueta.setAttribute("y", quintas ? 12 : 120);
    for (const n of nodos) {
      n.lugar = lugar(n.g, modo);
      const x = n.lugar.r * Math.cos(n.lugar.a), y = n.lugar.r * Math.sin(n.lugar.a);
      n.grupo.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      const r = radioNodo(n.g, modo);
      for (const c of [n.base, n.estela, n.activo]) c.setAttribute("r", r);
      if (n.marca) n.marca.setAttribute("r", r + 8);
      const regular = n.g % 2 === 0;
      n.texto.setAttribute("y", regular ? 7 : 5);
      n.texto.style.opacity = regular || quintas ? "" : 0;   // en la cromática no caben los nombres «+»
    }
  }

  // ───────────── controles ─────────────
  const $ = (id) => document.getElementById(id);
  const boton = $("reproducir"), barraT = $("tiempo"), rotulo = $("reloj"), selPista = $("pista"), selVoz = $("voz"),
    velocidad = $("velocidad"), chkHuella = $("ver-huella"), chkAcordes = $("ver-acordes"), selDisp = $("disposicion");
  $("titulo").textContent = D.titulo;
  $("subtitulo").textContent = `${D.desde.toFixed(1)} s a ${D.hasta.toFixed(1)} s` + (D.tempo_bpm ? ` · ${Math.round(D.tempo_bpm)} BPM` : "") +
    (tonica !== null ? ` · tónica ${nombre24(tonica)}` : "");
  barraT.max = duracion;
  if (!D.voces.grave || !D.voces.grave.length) {
    for (const o of selVoz.options) if (o.value !== "aguda") o.disabled = true;
  }
  if (parametros.get("disposicion") === "quintas") selDisp.value = "quintas";
  colocar(selDisp.value);
  selDisp.addEventListener("change", () => colocar(selDisp.value));

  // Pistas que exportó Python. `audio` conserva compatibilidad con exportaciones antiguas.
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
  const disponible = (v) => (COMBINACIONES[v] || []).length > 0 && COMBINACIONES[v].every((n) => elementos[n]);
  for (const o of selPista.options) o.disabled = !disponible(o.value);
  const vozPorPista = { guitarra: "aguda", bajo: "grave", guitarra_bajo: "ambas", guitarra_bajo_bateria: "ambas", mezcla: "ambas" };
  const pedida = parametros.get("pista");
  const primera = [pedida, "guitarra_bajo", "guitarra", "bajo", "mezcla"].find((v) => v && disponible(v));
  if (primera) {
    selPista.value = primera;
    selVoz.value = parametros.get("voz") || vozPorPista[primera];
  } else {
    selPista.disabled = true;
    if (parametros.get("voz")) selVoz.value = parametros.get("voz");
  }
  const pistasActivas = () => (COMBINACIONES[selPista.value] || []).map((n) => elementos[n]).filter(Boolean);
  const usarAudio = () => pistasActivas().length > 0;

  let tPropio = 0, corriendo = false, ultimo = null;
  const ahora = () => Math.max(0, usarAudio() ? pistasActivas()[0].currentTime - inicioAudio : tPropio);
  const irA = (t) => {
    t = Math.min(Math.max(0, t), duracion);
    for (const a of pistasActivas()) a.currentTime = inicioAudio + t;
    tPropio = t;
  };
  const sonar = () => {
    for (const a of pistasActivas()) {
      a.playbackRate = parseFloat(velocidad.value);
      a.play().catch(() => {});
    }
  };
  const reproducir = () => {
    if (ahora() >= duracion - 0.01) irA(0);
    corriendo = true;
    boton.textContent = "Pausa";
    if (usarAudio()) sonar();
  };
  const pausar = () => {
    corriendo = false;
    boton.textContent = "Reproducir";
    for (const a of Object.values(elementos)) a.pause();
  };
  boton.addEventListener("click", () => (corriendo ? pausar() : reproducir()));
  barraT.addEventListener("input", () => irA(parseFloat(barraT.value)));
  velocidad.addEventListener("change", () => { for (const a of pistasActivas()) a.playbackRate = parseFloat(velocidad.value); });
  selPista.addEventListener("change", () => {
    const t = ahora();
    for (const a of Object.values(elementos)) a.pause();
    if (vozPorPista[selPista.value]) selVoz.value = vozPorPista[selPista.value];
    irA(t);
    if (corriendo) sonar();                    // si estaba sonando, sigue sonando con la pista nueva
  });
  document.addEventListener("keydown", (e) => {
    const tag = e.target.tagName;
    if (e.code === "Space" && !["INPUT", "SELECT", "BUTTON"].includes(tag)) {   // un botón con foco ya responde a la barra
      e.preventDefault();
      corriendo ? pausar() : reproducir();
    } else if (embebido && ["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp", "PageDown", "PageUp"].includes(e.key) && tag !== "INPUT") {
      try {                                     // en la presentación, las flechas siguen cambiando de diapositiva
        const R2 = window.parent.Reveal;
        if (R2) { e.preventDefault(); ["ArrowRight", "ArrowDown", "PageDown"].includes(e.key) ? R2.next() : R2.prev(); }
      } catch (_) { /* otra procedencia: se ignora */ }
    }
  });
  window.addEventListener("message", (e) => { if (e.data === "circulo24:pausar") pausar(); });
  for (const a of Object.values(elementos)) a.addEventListener("loadedmetadata", () => irA(ahora()));

  // ───────────── animación ─────────────
  const voces = () => (selVoz.value === "ambas" ? ["aguda", "grave"] : [selVoz.value]);
  const fmt = (s) => `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`;

  function dibujarAcorde(grados) {
    while (capaAcorde.firstChild) capaAcorde.removeChild(capaAcorde.firstChild);
    if (!chkAcordes.checked || grados.length < 2) return;
    const puntos = grados.map((g) => { const p = nodos[g].lugar; return [p.r * Math.cos(p.a), p.r * Math.sin(p.a)]; });
    if (puntos.length === 2) {
      el("line", { x1: puntos[0][0], y1: puntos[0][1], x2: puntos[1][0], y2: puntos[1][1], class: "acorde" }, capaAcorde);
    } else {
      const cadena = puntos.concat([puntos[0]]).map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
      el("polyline", { points: cadena, class: "acorde" }, capaAcorde);
    }
  }

  function cuadro(ts) {
    if (corriendo && !usarAudio() && ultimo !== null) tPropio += ((ts - ultimo) / 1000) * parseFloat(velocidad.value);
    ultimo = ts;
    if (corriendo && usarAudio()) {            // las pistas que suenan juntas se mantienen alineadas con la primera
      const [ref, ...otras] = pistasActivas();
      for (const a of otras) if (Math.abs(a.currentTime - ref.currentTime) > 0.06) a.currentTime = ref.currentTime;
    }
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
    const maximoRegular = Math.max(...acumulado.filter((_, g) => g % 2 === 0), 1e-9);
    const maximoCuarto = Math.max(...acumulado.filter((_, g) => g % 2 === 1), 1e-9);
    const quintas = selDisp.value === "quintas";
    const maximo = Math.max(maximoRegular, maximoCuarto);
    for (const n of nodos) {
      const g = n.g, v = activo[g];
      n.activo.setAttribute("opacity", v ? 1 : 0);
      if (v) n.activo.setAttribute("fill", COLOR[v]);
      n.estela.setAttribute("opacity", v ? 0 : estela[g].toFixed(3));
      n.texto.classList.toggle("encendido", !!v);
      // Huella: hacia afuera desde R_HUELLA; en «quintas», la de los cuartos de tono va entre los dos anillos.
      const interna = quintas && g % 2 === 1;
      const inicio = interna ? R_INTERNO + 26 : R_HUELLA;
      const largo = chkHuella.checked ? ((interna ? LARGO_INTERNO : LARGO_HUELLA) * acumulado[g]) / maximo : 0;
      const { a } = n.lugar;
      n.barra.setAttribute("x1", (inicio * Math.cos(a)).toFixed(1));
      n.barra.setAttribute("y1", (inicio * Math.sin(a)).toFixed(1));
      n.barra.setAttribute("x2", ((inicio + largo) * Math.cos(a)).toFixed(1));
      n.barra.setAttribute("y2", ((inicio + largo) * Math.sin(a)).toFixed(1));
      n.barra.style.opacity = largo > 0.5 ? "" : 0;
    }
    etiqueta.textContent = [...new Set(sonando)].join(" · ");
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(cuadro);
})();
