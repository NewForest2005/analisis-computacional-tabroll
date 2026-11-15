# Corpus abiertos para situar a Angine de Poitrine

## ¿Estilo existente o propuesta nueva?

Ningún corpus abierto localizado cubre a la vez los tres rasgos que distinguen a la banda:

- raíces armónicas recurrentes I–♭III–♭VII, con acordes de potencia y suspendidos;
- grados neutros fijos de cuarto de tono en la melodía;
- compases irregulares, especialmente de 5 y 7 tiempos.

Sí existen corpus que permiten medir cada dimensión frente a sus vecinos plausibles. La comparación debe hacerse por
bloques y después de forma conjunta:

1. raíces y transiciones armónicas;
2. alturas microtonales, expresadas en 12/24 clases o en cents;
3. metro y estructura rítmica.

La hipótesis más interesante es que la banda puede ser típica en cada dimensión de un corpus distinto, pero atípica en
la combinación de las tres: una recombinación nueva de lenguajes existentes.

## Hallazgos provisionales

La armonía I–♭III–♭VII, los acordes de potencia y los acordes suspendidos son compatibles con el rock y el metal. Los
grados neutros sobre un entorno frigio acercan la melodía a makam/maqam y a otras tradiciones microtonales. Los compases
de 5 y 7 y la construcción por capas la acercan al prog, al aksak/usul y a la música de loops.

La comparación de Sarniezz sugiere una separación importante:

- la armonía es convencional y pentatónica, con ciclos fuertes y poca microtonalidad en las fundamentales;
- la microtonalidad vive principalmente en la melodía y aparece como cromatismo extendido;
- los pasos de tres cuartos de tono son escasos, por lo que la semejanza con maqam no debe afirmarse solo por la presencia
  de cuartos de tono.

Fabienk muestra el mismo perfil de manera más suave: armonía pentatónica y cíclica, melodía modal y poca microtonalidad
medida por el cuaderno.

Estas conclusiones siguen siendo provisionales porque el cuaderno puede perder o redondear notas microtonales. La
precisión de la melodía medida hasta ahora está aproximadamente entre 45 y 66 % según la canción.

## Corpus recomendados

### Tradiciones microtonales y modales

**SymbTr** es la referencia simbólica principal para makam turco. Contiene aproximadamente 2200 piezas, 155 makams,
88 usuls y unas 865 000 notas, con alturas en comas de Holder (53 divisiones). El usul aporta información métrica,
incluidos ciclos irregulares. Debe compararse en bins de 53 y, solo como aproximación, reducirse a 24 o 12 clases.

**Radif Corpus / ShourCorpus** ofrece repertorio persa con koron y sori codificados mediante pitch bend. Es especialmente
útil para la comparación 24-EDO, aunque la práctica instrumental persa no se reduce completamente a 24 divisiones.
El corpus principal contiene 228 piezas y 43 441 notas, según sus autores.

Para música árabe no se localizó un corpus simbólico abierto equivalente. El corpus arabo-andaluz de CompMusic es el
sustituto más cercano: combina partituras MusicXML, metadatos y distribuciones de altura extraídas de audio.

Saraga, OTMM y Erkomaishvili son alternativas de audio para comparar perfiles de altura en cents, no sustitutos directos
de una partitura de 24-EDO.

### Rock, metal, prog y pop

**Chordonomicon** permite filtrar grandes cantidades de canciones por subgénero de rock. Es adecuado para raíces,
acordes y transiciones, pero sus acordes son absolutos y no siempre incluyen tonalidad fiable.

**DadaGP** y **ProgGP** son más cercanos a riffs, guitarra, bajo y compases de rock/prog, aunque el acceso a los datos
completos puede requerir solicitud y sus licencias deben revisarse antes de redistribuirlos.

**Hooktheory/SheetSage** aporta acordes, melodía, tonalidad y metro en un formato muy útil para ampliar el corpus pop.
El corpus Pop local del proyecto sirve como referencia inicial, pero SheetSage permitiría aumentar considerablemente la
muestra.

### Jazz, clásica y folk

La **Weimar Jazz Database** permite comparar solos modales, blues y cambios armónicos usando SQLite y metadatos de
tonalidad.

El **DCML Distant Listening Corpus** y *When in Rome* ofrecen análisis RomanText/TSV de música clásica, incluyendo
Debussy y Bartók. Son adecuados para contrastar armonía modal, cromatismo y metro, pero no son corpus microtonales.

**The Session** y **Essen** permiten comparar repertorio modal, pentatónico y metros irregulares de tradición folk.

## Método de comparación

Los adaptadores del proyecto normalizan los corpus de armonía a una interfaz común:

- fundamentales relativas a la tónica en 12 clases;
- transiciones entre fundamentales;
- distribución de piezas y tamaño de cada corpus.

La similitud armónica se expresa como una distancia de Jensen–Shannon y, para las gráficas, como:

```text
similitud = 100 × (1 − distancia)
```

Así Rock, clásica, Jazz y Pop quedan en una escala comparable. Las métricas microtonales y rítmicas se mantienen en
bloques separados: no deben mezclarse con una distribución tonal de 12 clases.

Para una evaluación formal conviene calcular una verosimilitud o percentil por bloque y después una medida conjunta. Si
la canción cae dentro de un corpus en armonía, dentro de otro en microtonalidad y dentro de un tercero en metro, pero no
cae dentro de ninguno en la combinación completa, la tesis puede sostener empíricamente la idea de un estilo híbrido.

## Límites y advertencias

- El radar descriptivo no pone todas sus puntas en la misma escala; sirve para ver perfiles, no para comparar directamente
  dos números de puntas distintas.
- El radar de corpus sí usa una escala común, pero depende de cómo se normalicen tonalidad, duración y transiciones.
- Los corpus de Rock, Chordonomicon, DadaGP y Hooktheory contienen sesgos de selección y transcripción.
- Los corpus microtonales simbólicos no representan necesariamente la afinación real de una interpretación.
- El radar rítmico describe rasgos del cuaderno; no es todavía una similitud estadística con math rock, prog o minimalismo.
- Antes de redistribuir datos crudos hay que comprobar la licencia de cada corpus. Para el repositorio de la tesis conviene
  publicar agregados, hashes, scripts y referencias, no los conjuntos completos cuando la licencia no lo permita.

## Referencias

### Sitios y datos

- [Rock Corpus / RS 200](https://rockcorpus.midside.com/), análisis armónicos, transcripciones melódicas y timing del
  corpus basado en la lista de Rolling Stone.
- [SymbTr, MTG](https://github.com/MTG/SymbTr) y [CompMusic](https://compmusic.upf.edu/node/140), corpus simbólico de
  makam turco.
- [Turkish Makam Melodic Phrase Dataset](https://doi.org/10.5281/zenodo.1283344).
- [OTMM Makam Recognition Dataset](https://doi.org/10.5281/zenodo.58413).
- [Corpus arabo-andaluz de CompMusic](https://github.com/MTG/arab-andalusian-music), con partituras y recursos de
  audio asociados en Zenodo.
- [Radif Corpus en Zenodo](https://doi.org/10.5281/zenodo.15742125) y [ShourCorpus](https://github.com/maziarkanani/ShourCorpus).
- [Saraga](https://doi.org/10.5281/zenodo.4301737).
- [Erkomaishvili Dataset](https://doi.org/10.5281/zenodo.6900390).
- [Chordonomicon](https://huggingface.co/datasets/ailsntua/Chordonomicon).
- [DadaGP](https://github.com/dada-bots/dadaGP) y [ProgGP](https://github.com/otnemrasordep/ProgGP).
- [SheetSage / Hooktheory](https://github.com/chrisdonahue/sheetsage).
- [Weimar Jazz Database](https://jazzomat.hfm-weimar.de/download/download.html).
- [DCML Distant Listening Corpus](https://github.com/DCMLab/distant_listening_corpus).
- [The Session data](https://github.com/adactio/TheSession-data).
- [Essen Folksong Collection](https://github.com/ccarh/essen-folksong-collection).
- [MTC Features / Essen](https://doi.org/10.5281/zenodo.3551003).
- [Kostka–Payne corpus y estadísticas](https://davidtemperley.com/kp-stats/).
- [iRealPro Corpus of Jazz Standards](https://doi.org/10.5281/zenodo.3546040).

### Papers y libros

- Trevor de Clercq y David Temperley, “A Corpus Analysis of Rock Harmony”, *Popular Music* 30(1), 2011.
- David Temperley, “A Statistical Analysis of Tonal Harmony”, 2009.
- Stefan Kostka y Dorothy Payne, *Tonal Harmony*, 3.ª ed., McGraw-Hill, 1995.
- Yuri Broze y Daniel Shanahan, “Diachronic Changes in Jazz Harmony”, *Music Perception* 31(1), 2013.
- Kantarelis et al., artículo y datos de **Chordonomicon**, 2024.
- Sarmento et al., artículo de **DadaGP**, ISMIR 2021.
- Loth et al., artículo de **ProgGP**, CMMR 2023.
- Kanani et al., “Radif Corpus”, arXiv:2507.10456, 2025.
- Karaosmanoğlu, documentación y publicación de **SymbTr**, ISMIR 2012.

Las licencias y tamaños deben verificarse de nuevo al descargar nuevas versiones. Las cifras de tamaño incluidas aquí
son las reportadas por los registros o artículos citados, no una garantía sobre futuras versiones.
