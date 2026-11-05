# Dataset de aforamiento digital de plátano y banano

Para el entrenamiento del modelo YOLOv5 se utilizaron varias fuentes de imágenes etiquetadas a partir de la identificación inicial. Se aplicaron además algunos procesamientos que se describirán en su orden dentro del flujo de preparación del dataset definitivo.

## Paso 1. Identificación de fuentes

Se tomó como referencia fundamental el proyecto de detección de banano denominado banano-drone ([https://github.com/EazyHood/banano-uav](https://github.com/EazyHood/banano-uav)) y se ubicaron las fuentes de datos utilizadas por el proyecto. Adicionalmente se hizo una búsqueda en la web con ayuda de herramientas de inteligencia artificial de otras posibles fuentes que cumplieran con el tipo de fotografía en posición nadir, tanto para plantas de plátano como de banano. Se pudo identificar otras fuentes plausibles mediante palabras clave de búsqueda en Roboflow tales como Plantain Detection o Banana Detection.

| **Dataset** | **Autores** | **Identificado en** | **Enlace** | **Cantidad de archivos** | **Detalle imágenes iniciales** |
|---|---|---|---|---|---|
| Banana Tree detection Computer Vision Model | Elliot Su | Repositorio del proyecto banana-drone | https://universe.roboflow.com/elliot-su-mv7fl/banana-tree-detection | 1 Version | test: 38<br>train: 322<br>val: 39 |
| Detecting Plantain Crops Computer Vision Model | Michael Armah | Repositorio del proyecto banana-drone | https://universe.roboflow.com/michael-armah/detecting-plantain-crops/ | 3 versiones. Usada únicamente v3 | test: 7<br>train: 129<br>val: 12 |
| platano-lasuiza Computer Vision Dataset | Daniel F Tovar | Repositorio del proyecto banana-drone | https://universe.roboflow.com/daniel-f-tovar-r-s-workspace/platano-lasuiza | tres versiones: usadas las tres | test: 55<br>train: 1638<br>val: 114 |
| AI-Banana Mapping DS-v1 / DS-v2 (1) | Juan Camilo Garcia Braham | Búsqueda en la web | https://zenodo.org/records/20945958 | 2 versiones: Usadas ambas | test: 9195<br>train: 32701<br>val: 9410 |

(1) El objetivo de la investigación es la identificación de plantas enfermas por Sigatoka. Las imágenes son tiles de ortomosaicos de gran resolución. Ver detalles en procesamiento

## Paso 2. Descarga y formato

Los datasets se descargaron en **formato YOLO darknet**: imágenes más un .txt por imagen con clase x_centro, y_centro, ancho alto, normalizados que representan cada una de las etiquetas de la imagen. Ambos archivos dentro de cada partición del dataset. El formato YOLO del dataset preparado por Garcia Braham separa etiquetas e imagenes en una estructura de images/partition, labels/partition

## Paso 3. Procesamiento

En general, los diferentes datasets cuentan con todas sus imágenes debidamente etiquetadas, tal como se observa en las vistas previas de Roboflow. Adicionalmente se creó un script en Python que hace uso de la librería de manipulación de imágenes CV2 para dibujar las cajas que se identifican en las etiquetas. Se identificaron los tres casos siguientes, para los cuales se hace el procesamiento descrito.

| **Caso** | **Procesamiento** |
|---|---|
| Imágenes de ortomosaicos de baja resolución | Eliminación |
| Imágenes que no muestran plantas a la vista y poseen etiquetas defectuosas (ejemplo: carreteras etiquetadas) | Eliminación |
| Imágenes que contenían la etiqueta dibujada | Eliminación |
| Dataset de Garcia Braham | Reconstrucción + Clasificación y selección de candidatos + Recorte + etiquetado |

Como se observa en la tabla anterior, el procesamiento de los dos primeros casos consistió simplemente en descartar imágenes que podrían representar problemas para el entrenamiento del modelo. El procesamiento fuerte se hizo con el dataset de García Braham, pues su trabajo tiene un objetivo diferente. A continuación se describe dicho procesamiento.

- **Reconstrucción:** Mediante la nomenclatura de los nombres de los archivos se identifica que la procedencia de estos es la partición de varios ortomosaicos. Se crea un script en python que utiliza esta información para identificar los componentes de un ortomosaico y se reconstruyen un total de 1015 imágenes que corresponden a un total de 509 ortomosaicos identificados de acuerdo a la nomenclatura de los nombres. El hecho de que se reconstruyeran más imágenes que ortomosaicos esperados proviene del hecho de que todos poseen tiles faltantes y el script genera distintas imágenes por ortomosaico de celdas contiguas pero inconexas con respecto a otros conjuntos dentro del mismo ortomosaico. Se crearon scripts para identificar qué tiles faltaban para cada ortomosaico y se hicieron reportes de los resultados.

- **Clasificación:** Mediante estos reportes de celdas faltantes se clasificaron las imágenes reconstruidas (en general todas poseían huecos negros de las celdas no existentes) de acuerdo a la cantidad de celdas faltantes identificadas. También se identificaron imágenes sin huecos pero estas corresponden a sólo una o dos celdas.

- **Selección de candidatos:** De forma visual se examinaron cada una de las imágenes reconstruidas filtrando posibles candidatos a ser usados. Dicha calificación se realiza si en la reconstrucción se pueden observar plantas completas o parcialmente completas que puedan ayudar al entrenamiento. Los ortomosaicos reconstruidos, dado el objetivo del proyecto contienen pocas o una única planta. Esta selección inicial fue clasificada a su vez en visibles y no visibles, siendo la primera categoría aquella en que la(s) planta(s) se observa(n) completa(s) y la segunda categoría aquellas en que parte de la planta se pierde por alguna celda faltante. Como resultado el conjunto de imágenes candidatas final se reduce a 436. Donde solo 136 son clasificadas como visibles

- **Prueba de completación:** Se realiza un script para completar celdas faltantes mediante información de píxeles vecinos para las imágenes con plantas incompletas. La gran mayoría de imágenes resultantes resultan poco satisfactorias y se descarta esta completación sintética, además que los mejores resultados se obtienen en imágenes que contienen plantas completas.

- **Recorte:** Se recortaron las 136 imágenes clasificadas como visibles recuperando visibilidad de plantas completas. Mediante este procesamiento se descartaron varios candidatos y se conservaron finalmente 94 imágenes recuperadas.

- **Etiquetado:** Se llevaron estas imágenes recortadas a la herramienta de Roboflow y se etiquetan de manera manual al formato de cajas de YOLO. El dataset se particiona a porcentajes similares a los vistos en los descargados 10%-10-80% para test-val-train respectivamente.

## Paso 4. Unificación de etiquetas

Cada conjunto de datasets proviene de un modelo de visión artificial para identificación de un solo tipo de planta, ya sea plátano o banano, por lo tanto, todas las etiquetas tienen el valor de clase igual a cero. Para el entrenamiento del modelo se desea distinguir entre ambos tipos de plantas y se definen las clases: 0 = plátano y 1 = banano (data.yaml). De este modo se realizan las siguientes manipulaciones sobre los archivos de etiquetas

- Los datasets de plátano conservan la clase 0.

- Los de banano, incluyendo el reconstruido y etiquetado en Roboflow, se reetiquetan sus clases a 1

## Paso 5. Redimensionado

El tamaño de imágenes de los distintos datasets son 640x640, 1024x1024 y un poco mayores pero rectangulares como en el caso del dataset platano-la-suiza. Los “ortomosaicos” reconstruidos poseen una resolución mucho más elevada, pero dado el interés del estudio original, son fotos en general a muy baja altura y por lo tanto con mucho detalle de la planta. Se decide por lo tanto reducir el tamaño de estas imágenes a una dimensión de 1024px (conservando su relación de aspecto) y con miras a realizar el entrenamiento con entradas de 864x864 px.

## Paso 6. Fusión en un dataset único

Para el entrenamiento se centraliza el dataset con una estructuración de carpetas del tipo images/partition, labels/partition. Se desarrolló un script scripts/merge_dataset.py que acepta las tres estructuras habituales de YOLO/Roboflow (images/train, train/images o train/) y detecta las particiones train, val/valid y test de cada subconjunto de datos y mueve imágenes y etiquetas de todas las fuentes a la estructura común previamente descrita, **respetando la partición original de cada fuente.**

## Paso 7. Aumento de datos

Mediante un conteo inicial de los conjuntos de datos, se observa que el resultado combinado está desbalanceado, siendo el número de imágenes para plátano cerca de cuatro veces superior al de imágenes de banano. Se construye por lo tanto un script de aumentación que busca equilibrar esta clase, creando nuevas muestras dentro de la partición de entrenamiento: scripts/banana_augmentation.py. Este script genera **3 copias aumentadas** de cada imagen aplicando las transformaciones (Mediante la librería Albumentations): volteo horizontal (p = 0,5), brillo y contraste aleatorios (p = 0,2) y desenfoque leve (p = 0,1). Las cajas se transforman junto con la imagen para asegurar el correcto etiquetado de las nuevas imágenes.

## Resultado final

El resultado final es un dataset balanceado en el número de imágenes para cada clase constituido por un total de 3378 imágenes con sus respectivas etiquetas con la siguiente partición de conjuntos de entrenamiento, prueba y validación.

| **Partición** | **Total imágenes etiquetadas** | **Porcentaje (%)** |
|---|---|---|
| test | 95 | 2.81 |
| train | 3140 | 92.95 |
| val | 143 | 4.29 |
| **TOTAL** | **3378** | **100** |

## Notas

Los scripts para la preparación del dataset están segmentados en dos repositorios de código distinto.

Repositorio 1. [https://github.com/afflorezc/aforamiento-app-dataset](https://github.com/afflorezc/aforamiento-app-dataset): Con los scripts para el preprocesamiento y preparación descrito en las etapas de reconstrucción - clasificación - selección y prueba de completación sintética para seleccion final, recorte y etiquetado manual. Adicionalmente se cuenta con un script para visualizar las etiquetas sobre las imágenes utilizado para generar las muestras del repositorio y ayudar en la eliminación de algunas de las imágenes mal etiquetadas de los otros conjuntos.

Repositorio 2. [https://github.com/JuanMauwu/aforamiento-digital-platano](https://github.com/JuanMauwu/aforamiento-digital-platano): Con los scripts para el entrenamiento, validación y pruebas de la predicción del modelo. Contiene adicionalmente los scripts auxiliares de las etapas finales de la preparación del dataset: aumentación y compresión de imágenes.
