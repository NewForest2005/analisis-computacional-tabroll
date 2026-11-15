# Evolución de la tesis

**Pregunta:** ¿la música de Angine de Poitrine encaja en un estilo existente o es una propuesta nueva? Se responde analizando por computador los círculos armónicos y los ciclos melódicos de sus canciones.

Canciones analizadas: Mata Zyklek, Sarniezz, Fabienk, Yor Zarad y Utzp. Comparación: Primus (Tommy the Cat, My Name Is Mud, Jerry Was a Race Car Driver).

Lo que sigue va en orden. Cada paso dice qué se hizo, qué salió y qué se descartó.

---

## 1. La herramienta: un cuaderno que transcribe en 24-EDO

- La banda toca en cuartos de tono (24 notas por octava). Ninguna herramienta estándar transcribe así, de modo que se armó un cuaderno propio.
- El cuaderno separa la guitarra y el bajo con Demucs, sigue la altura con saliencia y Viterbi, saca las notas, los compases y los ciclos del looper, y analiza la armonía por compás.
- Produce el tabroll (al estilo de Hooktheory), el círculo armónico y los ciclos melódicos.
- El cuaderno empezó en Colab y pasó a GitHub porque se acababa la RAM. Cada celda tiene su copia en `src/tabroll/cells/`.

## 2. Cómo saber si la herramienta acierta

- **Primera idea: comparar contra la partitura oficial de Guitar Pro.** Se descartó como criterio, porque la partitura también se equivoca y la de Fabienk es de la versión en vivo. Quedó solo como comparación.
- **Criterio adoptado: partituras corregidas de oído por el autor**, con clips de la grabación contra la partitura sintetizada. Así se hicieron Sarniezz y Fabienk (9-nov); Mata Zyklek se tomó de la transcripción de la sesión de KEXP.
- **Medida:** F de notas, con ataque a ±75 ms y altura a ±25 cents, es decir, la misma casilla de 24-EDO. Se mide para la melodía principal (elegida por el autor en cada sección) y para el bajo.
- **Arbitraje a ciegas** donde el cuaderno y la partitura no coinciden: el autor elige entre versiones en orden al azar, con controles y con la regla fijada antes de escuchar.
  - Ronda 1 (13-nov): en la mitad de los casos tenía razón la partitura. Un desacuerdo no basta para corregir.
  - Ronda 2 (14-nov): tres notas de Sarniezz, una pista de Fabienk y una nota de Mata Zyklek corregidas.
- **Reproducibilidad (13-nov):** Demucs con semilla fija y huellas de los archivos. Con dos separaciones distintas, la misma canción daba 57 y 62: un hallazgo solo cuenta si se mantiene con las dos.
- **Se quitó todo lo que usaba la partitura para guiar el análisis** (el selector de pista por el .gp y los ajustes por canción). La herramienta tiene que servir con canciones sin partitura.

## 3. La línea melódica: qué se probó

Resultado actual (F de la melodía principal): Mata Zyklek 66.4, Fabienk 46.2, Sarniezz 44.9. Bajo: 83.0, 69.2 y 78.6.

| Idea | Qué pasó | Estado |
|---|---|---|
| Consenso entre vueltas del looper | Más rápido y más estable | Adoptada |
| Atracción al registro de la melodía | Sube Mata Zyklek de 57 a 64 | Adoptada |
| Quitar notas sueltas | +3 puntos en las tres canciones | Adoptada |
| Guiar con la partitura (.gp) | Prohibido por las reglas; además no mejoraba de forma estable | Descartada |
| Unir notas iguales seguidas | Borra re-ataques reales | Descartada |
| REPET (separar lo que se repite en el loop) | Solo deja el 1–18 % de la melodía en primer plano | Descartada |
| Elegir la capa más nueva del looper | Funciona sobre la partitura, falla sobre el audio | Descartada |
| Estéreo por canal | La melodía sigue tapada en la mitad de los cuadros | Descartada |
| Basic Pitch (Spotify) | Encuentra menos melodía y no da cuartos de tono | Descartada |
| Votar la altura entre vueltas, refinar por armónicos, prueba de octava, otros umbrales | Ninguna mejora las tres canciones a la vez | Descartadas |
| Bajar el piso de la voz aguda | Empeora las tres canciones | Descartada; queda por probar un piso que baje solo en los riffs graves |

## 4. La prueba a ciegas

- **Yor Zarad** se reservó sin abrir ninguna salida del cuaderno. La referencia se armó con las tablaturas de los PDF y los audios por pista de Guitar Pro, y la verificó el autor de oído (26 clips, 6 de ellos a ciegas).
- **Medida única:** melodía principal 36.8, sin contar la octava 47.7, bajo 68.6. El centro de la canción está al nivel de las otras (48–67).
- **Fallo encontrado:** el riff grave sale una octava arriba, porque la voz aguda nunca baja de Si2. El autor confirmó a ciegas que la referencia tenía razón.
- **Utzp** era la segunda prueba a ciegas. Su referencia no pasó la verificación de oído (ritmo de las guitarras de acordes) y se aparcó. Después se usó como una canción más.

## 5. La armonía

- Acorde por compás en 24-EDO: fundamental, calidad (incluidas las terceras neutras), grado, función (Riemann) y eje (Lendvai), con una medida de confianza.
- **Centro:** se descartó elegirlo automáticamente por el bajo, porque en Sarniezz y Fabienk el bajo descansa en ♭VII. Se usa el centro que coincide con el oído.
- **Referencia completa (14-nov):** se sumaron todas las guitarras de Guitar Pro a la referencia corregida. La medida casi no cambió (+0 a +1.3 puntos), así que la de antes era representativa.
- **Fundamental correcta:** Mata Zyklek 95 %, Fabienk 82–83 %, Sarniezz 58 %. Sarniezz es el punto débil, por su riff cromático de cuartos de tono.
- **Arreglo con Primus:** la confianza castigaba los compases fuera de ciclo, así que una canción sin looper salía con el 20 % confiable. Se arregló (sin ciclos, no se castiga) y pasó al 50–72 %.
- **Límite que sigue abierto:** fuera de la banda falla la elección del centro (Tommy the Cat sale en Sol en vez de Mi).

## 6. Comparación con estilos

Se probó en este orden:

1. **Pop: 9 álbumes analizados por Hooktheory.** La banda queda lejos (distancia 0.40–0.59, cuando los álbumes entre sí no pasan de 0.07).
2. **Tarjetas al estilo de Hooktheory.** Las cinco métricas de Hooktheory son percentiles contra su base de 40 000 canciones y no se pueden recalcular, así que se usan valores crudos y las de Hooktheory solo como contexto. Hooktheory tiene una sola canción de la banda (el riff de Fabienk).
3. **Pruebas de estilo con reglas y cifras publicadas** (rock, práctica común, jazz, pentatónica, tonos enteros, dodecafonismo, minimalismo, microtonal). Sirvieron para descartar: jazz, práctica común, tonos enteros y dodecafonismo no encajan en ninguna canción. Problema: los umbrales los propuse yo.
4. **Matriz de verosimilitud con corpus**, que reemplazó a los umbrales: rock (Rolling Stone 200), práctica común (Kostka-Payne), jazz (iRealPro, 1 186 estándares) y pop. Cada canción se ubica dentro de la distribución real de cada estilo.
   - Ninguna canción de la banda es típica de ningún estilo: todas quedan bajo el percentil 18, y tres de ellas bajo el 8.
   - Las canciones de pedal (Mata Zyklek, Utzp) quedan en el borde del rock. Sarniezz y Fabienk caen donde no hay piezas de ningún corpus (mucho ♭VII y ♭III).
5. **Radares** con una punta por estilo, separados en armonía, melodía y ritmo. La primera versión tenía cada punta en su propia escala; ahora las de estilo usan la verosimilitud.

## 7. Los cuartos de tono

- **Primera lectura, equivocada:** la punta microtonal salía baja. Se medía solo la cantidad, y las fundamentales de los acordes casi nunca caen en cuarto de tono.
- **Piso de ruido:** en Primus, que no usa cuartos de tono, el cuaderno marca el 9–13 % de la melodía en cuartos de tono (bends, slides).
- **La división adorno/grado por duración no sirvió:** Primus también da «grados».
- **Lo que sí separa a la banda es la concentración:** pone los cuartos de tono en uno o dos grados fijos (48–82 %) que vuelven en casi todas las vueltas del ciclo. En Primus están repartidos (28–37 %).
- **Dos familias de escala:**
  - ♭2+ y ♭6+ sobre un frigio (Mata Zyklek, Yor Zarad, Utzp), cercana al maqam y al makam turco, que la banda cita.
  - 7+, 6+ y ♭3+ sobre un dórico (Sarniezz, Fabienk).

## 8. Primus como influencia

- **Comparación por tarjetas, partituras y cuaderno:**
  - Tommy the Cat comparte con Fabienk y Sarniezz el centro, el modo dórico y las fundamentales 1, ♭3 y ♭7.
  - My Name Is Mud es un pedal, como Mata Zyklek.
- **Diferencias:** Primus no tiene ciclos de looper ni cuartos de tono concentrados, y cambia más de acorde.
- **Aviso:** ninguna fuente pública consultada cita a Primus como influencia de la banda. La banda cita rock turco, King Gizzard, Zappa, Gentle Giant y Scofield. Se presenta como comparación propia.

## 9. Lo descartado o aparcado

- **Comparar con escuelas clásicas concretas** (vienesa, alemana, francesa), impresionismo y Gershwin: no hay corpus descargables. Solo hay rasgos cualitativos.
- **La referencia de Utzp:** falta leer la figuración rítmica del pentagrama.
- **La genealogía completa de influencias:** queda para después de la segunda influencia.
- **La síncopa del radar rítmico:** con la regla actual da lo mismo que el azar.

## 10. Respuesta provisional

La banda es un **híbrido con un elemento nuevo**:

- **Armonía:** fundamentales de rock modal-pentatónico, sin dominante, pero desplazadas hacia ♭VII y ♭III, a una zona que ningún corpus ocupa.
- **Forma:** ciclos repetidos de looper, como el minimalismo y el techno, con compases irregulares en la mitad de las canciones, como el math rock.
- **Melodía:** escalas propias de 24 notas, con grados neutros fijos (♭2+, ♭6+, 6+, 7+, ♭3+), emparentadas con el maqam. Ningún estilo medido los tiene. Esto es lo nuevo.

**Límites:** la melodía del cuaderno acierta entre 37 y 66 %; la armonía de Sarniezz, el 58 %; hay pocas canciones; y los corpus no tienen cuartos de tono.
