# Referencias compiladas del proyecto

Este documento reúne las referencias bibliográficas, metodológicas, corpus, fuentes sobre Angine de Poitrine y recursos
consultados durante el desarrollo del análisis computacional microtonal, las gráficas del póster y los documentos
matemáticos elaborados. Las entradas marcadas «por verificar» requieren comprobación final antes de una entrega formal.

## Documentos internos de referencia

- README.md: descripción general del repositorio, corpus y scripts.
- docs/corpus_estilos.md: corpus abiertos, método de comparación y límites.
- docs/verosimilitud_por_bloques.md: interpretación de los bloques de armonía, escala, cuartos de tono y metro.
- docs/guion_defensa.md: guion de la defensa por diapositiva, con los términos de cada una (por ahora, diapositivas 12 a 23).
- Corridas congeladas `outputs/*_repro` (13-nov-2026): fuente de las cifras de acierto de la diapositiva 18 y del glosario.
- docs/glosario.md: glosario de la presentación (24-EDO, MIDI, MIDI fraccionario, perfil de 24 clases, MFCC, pYIN, desviación en cents, piano roll, compás, funciones de Riemann, ejes de Lendvai…).
- docs/armonia.md: fundamentos de armonía, funciones, progresiones, Piston, Riemann y Lendvai.
- docs/evaluacion_melodia.md: evaluación de melodía, alineaciones y referencias anotadas.
- docs/evolucion_de_la_tesis.md: evolución conceptual y bibliográfica del proyecto.
- references/referencias_completas.md: base bibliográfica original, incorporada íntegramente desde la sección siguiente.
- trabajo/historial_commits_cuaderno.txt: historial del desarrollo y procedencia de las etapas del análisis.
- docs/poster/LEEME_nuevos_graficos.md: contenido propuesto para introducción, metodología, resultados, perspectivas y conclusiones del póster.
- docs/formulas/formulas_teoria_matematica_angine_de_poitrine.pdf: resumen de fórmulas de tono logarítmico, Mel, Fourier, MFCC, KL y repetición temporal.

## Referencias bibliográficas y fuentes

Verificadas durante la investigación, salvo las marcadas «por verificar». Antes de enviar, contrastar cada DOI en Crossref: TISMIR rechaza referencias inexistentes o incorrectas.

**Extracción, separación y estructura**

- Bittner, R. M., Bosch, J. J., Rubinstein, D., Meseguer-Brocal, G., y Ewert, S. (2022). A lightweight instrument-agnostic model for polyphonic note transcription and multipitch estimation. *Proc. IEEE ICASSP*, 781-785. https://doi.org/10.1109/ICASSP43922.2022.9746549

- Ellis, D. P. W. (2007). Beat tracking by dynamic programming. *Journal of New Music Research*, 36(1), 51-60. https://doi.org/10.1080/09298210701653344

- Foote, J. (2000). Automatic audio segmentation using a measure of audio novelty. *Proc. IEEE ICME*, 452-455. https://doi.org/10.1109/ICME.2000.869637

- Kim, J. W., Salamon, J., Li, P., y Bello, J. P. (2018). CREPE: A convolutional representation for pitch estimation. *Proc. IEEE ICASSP*. https://doi.org/10.1109/ICASSP.2018.8461329

- Lu, W.-T., Wang, J.-C., Kong, Q., y Hung, Y.-N. (2024). Music source separation with band-split RoPE transformer. *Proc. IEEE ICASSP*, 481-485. https://doi.org/10.1109/ICASSP48485.2024.10446843

- Mauch, M., y Dixon, S. (2014). pYIN: A fundamental frequency estimator using probabilistic threshold distributions. *Proc. IEEE ICASSP*, 659-663. https://doi.org/10.1109/ICASSP.2014.6853678

- McFee, B., y Ellis, D. P. W. (2014). Analyzing song structure with spectral clustering. *Proc. ISMIR*, 405-410.

- McFee, B., Raffel, C., Liang, D., Ellis, D. P. W., McVicar, M., Battenberg, E., y Nieto, O. (2015). librosa: Audio and music signal analysis in Python. *Proc. SciPy*, 18-24. https://doi.org/10.25080/Majora-7b98e3ed-003

- Müller, M. (2015). *Fundamentals of Music Processing*. Springer. https://doi.org/10.1007/978-3-319-21945-5

- Paulus, J., Müller, M., y Klapuri, A. (2010). State of the art report: Audio-based music structure analysis. *Proc. ISMIR*, 625-636.

- Rafii, Z., y Pardo, B. (2013). REpeating Pattern Extraction Technique (REPET): A simple method for music/voice separation. *IEEE Transactions on Audio, Speech, and Language Processing*, 21(1), 71-82. https://doi.org/10.1109/TASL.2012.2213249

- Raffel, C., McFee, B., Humphrey, E. J., Salamon, J., Nieto, O., Liang, D., y Ellis, D. P. W. (2014). mir\_eval: A transparent implementation of common MIR metrics. *Proc. ISMIR*, 367-372.

- Rouard, S., Massa, F., y Défossez, A. (2023). Hybrid transformers for music source separation. *Proc. IEEE ICASSP*. https://doi.org/10.1109/ICASSP49357.2023.10096956

- Salamon, J., y Gómez, E. (2012). Melody extraction from polyphonic music signals using pitch contour characteristics. *IEEE Transactions on Audio, Speech, and Language Processing*, 20(6), 1759-1770. https://doi.org/10.1109/TASL.2012.2188515

- Serrà, J., Müller, M., Grosche, P., y Arcos, J. Ll. (2014). Unsupervised music structure annotation by time series structure features and segment similarity. *IEEE Transactions on Multimedia*, 16(5), 1229-1240. https://doi.org/10.1109/TMM.2014.2310701

**MIR microtonal**

- Bozkurt, B. (2008). An automatic pitch analysis method for Turkish maqam music. *Journal of New Music Research*, 37(1), 1-13.

- Bozkurt, B., Yarman, O., Karaosmanoğlu, M. K., y Akkoç, C. (2009). Weighing diverse theoretical models on Turkish maqam music against pitch measurements. *Journal of New Music Research*, 38(1), 45-70. https://doi.org/10.1080/09298210903147673
- Bozkurt, B., Ayangil, R., y Holzapfel, A. (2014). Computational analysis of Turkish makam music: Review of state-of-the-art and challenges. *Journal of New Music Research*, 43(1), 3-23.
- Gedik, A. C., y Bozkurt, B. (2010). Pitch-frequency histogram-based music information retrieval for Turkish music. *Signal Processing*, 90(4), 1049-1063. https://doi.org/10.1016/j.sigpro.2009.06.017
- Kanani, M., O'Leary, S., y McDermott, J. (2025). Radif Corpus: A symbolic dataset for non-metric Iranian classical music. *Proc. ISMIR*. [arXiv:2507.10456](https://arxiv.org/abs/2507.10456)
- Serra, X. (2011). A multicultural approach in music information research. *Proc. ISMIR*. (por verificar)

**Corpus, estilo y teoría de la información**

- Broze, Y., y Shanahan, D. (2013). Diachronic changes in jazz harmony: A cognitive perspective. *Music Perception*, 31(1), 32-45. https://doi.org/10.1525/mp.2013.31.1.32
- de Clercq, T., y Temperley, D. (2011). A corpus analysis of rock harmony. *Popular Music*, 30(1), 47-70. https://doi.org/10.1017/S026114301000067X
- Huron, D. (2006). *Sweet Anticipation: Music and the Psychology of Expectation*. MIT Press.
- Krumhansl, C. L. (1990). *Cognitive Foundations of Musical Pitch*. Oxford University Press.
- Lin, J. (1991). Divergence measures based on the Shannon entropy. *IEEE Transactions on Information Theory*, 37(1), 145-151. https://doi.org/10.1109/18.61115
- Pearce, M. T. (2018). Statistical learning and probabilistic prediction in music cognition: Mechanisms of stylistic enculturation. *Annals of the New York Academy of Sciences*, 1423(1), 378-395. https://doi.org/10.1111/nyas.13654
- Shanahan, D., Broze, Y., y Rodgers, R. (2012). A diachronic analysis of harmonic schemata in jazz. *Proc. ICMPC 12 / ESCOM 8*, 909-917.
- Temperley, D., y de Clercq, T. (2013). Statistical analysis of harmony and melody in rock music. *Journal of New Music Research*, 42(3), 187-204.

**Glosario: conceptos y teoría** (fuentes de [`docs/glosario.md`](glosario.md); Piston y Lendvai verificados en catálogos; las demás, por verificar)

- Christen, P., Hand, D. J., y Kirielle, N. (2024). A review of the F-measure: Its history, properties, criticism, and alternatives. *ACM Computing Surveys*, 56(3). https://doi.org/10.1145/3606367 (historia de la medida F; por verificar volumen y año)
- Davis, S. B., y Mermelstein, P. (1980). Comparison of parametric representations for monosyllabic word recognition in continuously spoken sentences. *IEEE Transactions on Acoustics, Speech, and Signal Processing*, 28(4), 357-366. https://doi.org/10.1109/TASSP.1980.1163420 (origen de los MFCC; por verificar)
- de Cheveigné, A., y Kawahara, H. (2002). YIN, a fundamental frequency estimator for speech and music. *Journal of the Acoustical Society of America*, 111(4), 1917-1930. https://doi.org/10.1121/1.1458024 (base de pYIN; por verificar)
- Lendvai, E. (1971). *Béla Bartók: An Analysis of His Music*. Kahn & Averill. ISBN 0900707046. (sistema de ejes)
- MIDI Manufacturers Association. (1996). *The Complete MIDI 1.0 Detailed Specification*. MMA. (estándar MIDI de 1983; por verificar)
- NIST (2015). *Secure Hash Standard (SHS)*. FIPS PUB 180-4. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.FIPS.180-4 (define SHA-256)
- Piston, W. (1987). *Harmony* (5.ª ed., revisada y ampliada por M. DeVoto). W. W. Norton. ISBN 0393954803. (calidades de acorde, grados tonales y modales, centro sin dominante; docs/armonia.md cita pp. 22-24 y 474)
- Riemann, H. (1893). *Vereinfachte Harmonielehre oder die Lehre von den tonalen Funktionen der Akkorde*. Augener. (teoría funcional; por verificar el año de la 1.ª edición alemana; trad. inglesa: *Harmony Simplified*, Augener, 1896)
- Stevens, S. S., Volkmann, J., y Newman, E. B. (1937). A scale for the measurement of the psychological magnitude pitch. *Journal of the Acoustical Society of America*, 8(3), 185-190. https://doi.org/10.1121/1.1915893 (escala Mel; por verificar)
- van Rijsbergen, C. J. (1979). *Information Retrieval* (2.ª ed.). Butterworths. (medida de efectividad E; la medida F es F = 1 − E)
- Viterbi, A. J. (1967). Error bounds for convolutional codes and an asymptotically optimum decoding algorithm. *IEEE Transactions on Information Theory*, 13(2), 260-269. https://doi.org/10.1109/TIT.1967.1054010 (por verificar)

**Ritmo y métrica**

- Holzapfel, A., Krebs, F., y Srinivasamurthy, A. (2014). Tracking the «odd»: Meter inference in a culturally diverse music corpus. *Proc. ISMIR*, 425-430.
- Loth, J., Sarmento, P., Carr, C. J., Zukowski, Z., y Barthet, M. (2023). ProgGP: From GuitarPro tablature neural generation to progressive metal production. *Proc. CMMR*. [arXiv:2307.05328](https://arxiv.org/abs/2307.05328)
- Sarmento, P., Kumar, A., Carr, C. J., Zukowski, Z., Barthet, M., y Yang, Y.-H. (2021). DadaGP: A dataset of tokenized GuitarPro songs for sequence models. *Proc. ISMIR*. arXiv:2107.14653
- Srinivasamurthy, A., Holzapfel, A., Cemgil, A. T., y Serra, X. (2016). A generalized Bayesian model for tracking long metrical cycles in acoustic music signals. *Proc. IEEE ICASSP*, 76-80. https://doi.org/10.1109/ICASSP.2016.7471640

**Datos**

- Karaosmanoğlu, M. K. (2012). A Turkish makam music symbolic database for music information retrieval: SymbTr. *Proc. ISMIR*, 223-228. [Repositorio](https://github.com/MTG/SymbTr)
- Shanahan, D., y Broze, Y. iRealPro Corpus of Jazz Standards (v1.0). Zenodo. https://doi.org/10.5281/zenodo.3546040
- Singh, Y., Gupta, Y., Patar, S., Saraswat, A., y Biswas, A. (2022). Hindustani Classical Music Transcription Dataset (v1.0.1). Zenodo. https://doi.org/10.5281/zenodo.7424861
- Kostka-Payne corpus (Temperley). (por verificar la cita de la fuente)
- Hooktheory, análisis de álbumes en bucles. (por verificar la cita de la fuente)

**Sobre las bandas (prensa y fuentes primarias)**

- Khn de Poitrine. «\[INTERVIEW\] Angine de Poitrine». *Aucard de Tours* (podcast), 26-feb-2026, 1:33–2:58. [Episodio](https://podcastaddict.com/aucard-de-tours/episode/218290057)
- *Guitar World*, sobre la guitarra microtonal de la banda. [Artículo](https://www.guitarworld.com/artists/bands/angine-de-poitrine-microtonal-guitar)
- *ABC News* (20-may-2026). [Artículo](https://www.abc.net.au/news/2026-05-20/angine-de-poitrine-microtonal-math-rock-quebec/106593634)
- King Gizzard and the Lizard Wizard (2017). *Flying Microtonal Banana*, nota de lanzamiento. [Página oficial](https://kinggizzardandthelizardwizard.com/release/flying-microtonal-banana)

**Fuentes audiovisuales y transcripciones de Angine de Poitrine**

La siguiente transcripción del podcast es una transcripción de trabajo corregida en francés. El tramo indicado es
1:33–2:58 del episodio; la palabra «ensemble» en «des riffs qui s’enchaînent ensemble» queda pendiente de confirmación
auditiva definitiva. No se presenta como una transcripción oficial.

> « Je dirais Angine de Poitrine, premièrement, c’est un duo guitare microtonale, basse microtonale et batterie. Puis on joue dans le rock, à saveur un peu électro. C’est pour dire que la musique est construite, est bâtie sur des loops, puis il y a quand même une répétitivité, mais toujours un build-up intentionnel pour apporter une phrase suivante, un riff plus développé, et s’en aller vers l’avant avec la tune, en ne restant pas stagnant […] une répétitivité — techno, c’est ça. Une touche électro ou techno au niveau de la construction structurelle des pièces, et non du timbre. Puis au niveau timbral, c’est plutôt ancré dans une tradition très rock, rock instrumental un peu champ gauche. […] pour faire danser les gens, rentrer un peu en transe avec ce délire de boucles, de riffs qui s’enchaînent ensemble. Idéalement les gens dansent en 5 puis en 7 […] toujours envie d’aller vers l’étrangeté, d’où l’utilisation peut-être du microtonal. »

- Mathémusique (Paul Lascabettes). « Comprendre ANGINE DE POITRINE », 16-may-2026. [YouTube](https://www.youtube.com/watch?v=96D7DKZh-es). Hacia el minuto 3:15 pone como precedente a King Gizzard and the Lizard Wizard (*Flying Microtonal Banana*, 2017), que también pasa de 12 a 24 notas.
- Monty, Adele, y Benabbou, Gabriel. « Angine De Poitrine: Interview with Infectious Quebec Band ». *Noize Magazine*, 20 de febrero (la página no indica el año). [Entrevista](https://www.noizemagazine.com/blog/angine-de-poitrine-a-discussion-with-the-infectious-quebec-band). Khn: rock turco y música de Medio Oriente, fraseo «a lo Zappa», armonía comparable al *Überjam* de John Scofield o a «So What» de Miles Davis, el looper los lleva cerca del techno. Klek: Gentle Giant es su banda favorita.
- McClain, Levi. Video sobre Angine de Poitrine, 7-sep-2026. [YouTube](https://www.youtube.com/watch?v=kWv5zjsjoHw).
- Little, Thomas (Classical Nerd). « The Quarter-Tone Problem (and Hába’s “Field Shifting” Solution) », 17-ene-2019. [YouTube](https://www.youtube.com/watch?v=E_Z0q7jqyqI).
- Bennett, David (David Bennett Music Theory). « How Angine de Poitrine use Microtonality », 21-mar-2026. [YouTube](https://www.youtube.com/watch?v=91QWp6Ygx7c). Hacia el minuto 7:20 dice que en uno de los temas los cuartos de tono se usan como en el maqam hijaz, «casi» el frigio dominante.

Correcciones recurrentes aplicadas al identificar nombres y términos en los tres videos: « Angine de Poitrine »
(no « engine », « Angile », « Anene Deontrine », « Angevin du Poitou » o « Angéline de Poitiers »); « Khn » (no
« Kuhn »); « Sarniezz »; « Utzp »; « Mata Zyklek »; « Fabienk »; y « Yor Zarad ». También se normalizan « quarts
de ton », « en sept temps », « quatre temps », « huit fois », « King Gizzard », « Sevish », « maqam Hijaz »,
« frigio », « microtonal », « Alois Hába » y « xenarmónico ». « Enorie », « Ababa hôtel » y « Cherpa/Sherper »
quedan sin identificar y no se deben citar como nombres confirmados.

## Recursos adicionales citados en la documentación de corpus

Estos recursos aparecen en docs/corpus_estilos.md como fuentes consultadas, recomendadas o posibles ampliaciones del
análisis; no todos fueron usados en las cifras finales:

- Digital Arabic Maqām Archive: https://diarmaqar.net/en
- ORD-CC32: https://zenodo.org/records/15682346
- Artículo de ORD-CC32: https://arxiv.org/abs/2506.14503
- Open Corpus for Arabic Maqam Recognition: https://lanfrica.com/en/record/open-corpus-for-arabic-maqam-recognition
- MaqamNet: https://github.com/josephbakarji/maqamnet
- Microtonal Music Dataset: https://www.komazawa-u.ac.jp/~thirai/MicrotonalMusicDataset/
- Artículo CMMR 2023 del Microtonal Music Dataset: https://zenodo.org/records/10113964/files/cmmr2023_4c-D4.pdf
- Análisis temporal de SymbTr y usul: https://github.com/eagomez2/turkish-makam-temporal-analysis
- Documentación de PyABC2 para The Session: https://pyabc2.readthedocs.io/en/stable/examples/sources.html
- Rock Corpus / Rolling Stone 200: https://rockcorpus.midside.com/
- CompMusic: https://compmusic.upf.edu/node/140
- Corpus arabo-andaluz de CompMusic: https://github.com/MTG/arab-andalusian-music
- Turkish Makam Melodic Phrase Dataset: https://doi.org/10.5281/zenodo.1283344
- OTMM Makam Recognition Dataset: https://doi.org/10.5281/zenodo.58413
- Radif Corpus en Zenodo: https://doi.org/10.5281/zenodo.15742125
- ShourCorpus: https://github.com/maziarkanani/ShourCorpus
- Saraga: https://doi.org/10.5281/zenodo.4301737
- Erkomaishvili Dataset: https://doi.org/10.5281/zenodo.6900390
- Chordonomicon: https://huggingface.co/datasets/ailsntua/Chordonomicon
- DadaGP: https://github.com/dada-bots/dadaGP
- ProgGP: https://github.com/otnemrasordep/ProgGP
- SheetSage / Hooktheory: https://github.com/chrisdonahue/sheetsage
- Weimar Jazz Database: https://jazzomat.hfm-weimar.de/download/download.html
- DCML Distant Listening Corpus: https://github.com/DCMLab/distant_listening_corpus
- The Session data: https://github.com/adactio/TheSession-data
- Essen Folksong Collection: https://github.com/ccarh/essen-folksong-collection
- MTC Features / Essen: https://doi.org/10.5281/zenodo.3551003
- Estadísticas del corpus Kostka--Payne: https://davidtemperley.com/kp-stats/
- iRealPro Corpus of Jazz Standards: https://doi.org/10.5281/zenodo.3546040

## Alcance y estado de las referencias

- Las referencias de papers, libros, fuentes primarias y datos fueron copiadas del inventario del proyecto y no se
  presentan aquí como una nueva verificación bibliográfica.
- Las fuentes marcadas «por verificar» deben comprobarse en Crossref, en el repositorio original o en la página oficial
  del recurso antes de citarlas en una tesis o artículo.
- Primus funciona en el proyecto como control de error de medición; King Gizzard, Frank Zappa, King Crimson y Gentle
  Giant funcionan como repertorios comparados, no como controles.
- TabRoll es una salida y una representación del repositorio, no un corpus externo ni una referencia bibliográfica.
