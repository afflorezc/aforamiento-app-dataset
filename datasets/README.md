# Muestra de datasets descargados

Este directorio cuenta con una muestra de las distintas imágenes originales que fueron 
descargadas de las diferentes fuentes, como también una muestra del dataset reconstruido. Se muestran a su vez sus etiquetas
correspondientes y la visualización de estas aplicando el script de visualization-test.py
sobre los distintos directorios. Se muestran también muestras de los mosaicos recuperados mediante
el scprit de reconstruct_mosaics.py.

En la carpeta zenodo-mosaics se tiene una muestra de los resultados de una clasificación de candidatos, 
el procesamiento de completación sintética probado y la clasificación final entre visibles y no visibles
descrito en la documentación de la preparación del dataset definitivo. La muestra de las imágenes finales seleccionadas,
recortadas y debidamente etiquetas se encuentran en la carpeta Banana Tree.v3i.yolov11. Las muestras de este repositorio
no contienen las imágenes generadas por métodos de aumentación aplicados, ni tampoco se encuentran comprimidas, por lo 
que los mosaicos reconstruidos tienen tamaños de mas de 4000px en su dimensión mayor. La aumentación se aplicó sobre
los mosaicos comprimidos inicialmente al redimensionar a un tamaño de 1024px en la dimensión mayor, conservando la relación
de aspecto.

## **NOTA**
Los scripts se presentan con las rutas absolutas y/o relativas utilizadas inicialmente en el procesamiento y 
preparación local.
