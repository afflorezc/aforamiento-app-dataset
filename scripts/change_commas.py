from pathlib import Path

archivo_csv = Path("17.csv")
archivo_txt = Path("17.txt")

with archivo_csv.open("r", encoding="utf-8") as entrada, \
     archivo_txt.open("w", encoding="utf-8") as salida:

    for linea in entrada:
        salida.write(linea.replace(",", " "))

print(f"Archivo guardado en: {archivo_txt}")