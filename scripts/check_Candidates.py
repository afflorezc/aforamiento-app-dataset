
import csv
import shutil
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────

REPORT_CSV = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates.csv")

CANDIDATES_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates")
MOSAICS_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics")

# Directorio de destino para los mosaicos completos.
DEST_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates")

# Si es True, solo muestra los archivos que movería.
# Cambia a False para ejecutar los movimientos.
DRY_RUN = False

def main():

    missed = []
    duplicates = []
    filenames = []
    missing = 0

    with REPORT_CSV.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        required_columns = {
            "folder", "date", "time", "weather", "picture",
            "part", "plants", "filename"
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Faltan columnas en el CSV: "
                f"{required_columns - set(reader.fieldnames or [])}"
            )

        for row in reader:

            filename = (row["filename"] or "").strip()

            if len(filenames) > 0 and filename in filenames:
                duplicates.append(filename)
            else:
                filenames.append(filename)

            source = Path(filename)
            source = CANDIDATES_DIR / source

            source = source if source.is_file() else None

            if source is None:
                print(f"[AVISO] el archivo {filename} no se movio")
                missed.append(filename)

                sub_dir = (row["folder"] or "").strip()

                if not sub_dir:
                    print(f"[AVISO] Sin Subdirectorio: {row['folder']}")
                    continue

                sub_dir = Path(sub_dir)
                source = Path(filename)
                source = MOSAICS_DIR / sub_dir / source

                source = source if source.is_file() else None

                if source is None:
                    print(f"[AVISO] No se pudo encontrar el archivo {filename}")
                    missing += 1
                  
                continue

            
    print("\n──── Resumen ────")

    print(f"Archivos totales: {len(filenames)}")
    print(f"Archivos duplicados en csv: {len(duplicates)}")

    if len(duplicates) > 0:
        for duplicate in duplicates:
            print(f"Archivo duplicado: {duplicate}")

    print(f"Archivos no movidos: {len(missed)}")
    print(f"Archivos perdidos: {missing}")

    if DRY_RUN:
        print("\nSimulación terminada. Si todo está correcto,")
        print("cambia DRY_RUN = False para mover los archivos.")


if __name__ == "__main__":
    main()