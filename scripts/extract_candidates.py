
import csv
import shutil
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────

REPORT_CSV = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates.csv")

# Directorio donde están guardados los mosaicos generados.
# Debe coincidir con la ubicación de los archivos de la columna output.
MOSAICS_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics")

# Directorio de destino para los mosaicos completos.
DEST_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates")

# Si es True, solo muestra los archivos que movería.
# Cambia a False para ejecutar los movimientos.
DRY_RUN = False

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    moved = 0
    missing = 0
    skipped = 0

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
            
            sub_dir = (row["folder"] or "").strip()

            if not sub_dir:
                print(f"[AVISO] Sin Subdirectorio: {row['folder']}")
                missing += 1
                continue

            sub_dir = Path(sub_dir)

            source = (row["filename"] or "").strip()

            if not source:
                print(f"[AVISO] Sin ruta de imagen")
                missing += 1
                continue

            source = Path(source)
            source = MOSAICS_DIR / sub_dir / source

            source = source if source.is_file() else None

            if source is None:
                print(f"[AVISO] el archivo {row['filename']} ya se ha movido")
                skipped += 1
                continue

            destination = DEST_DIR / source.name

            # Evitar sobrescribir archivos existentes.
            if destination.exists():
                print(f"[OMITIDO] Ya existe: {destination}")
                skipped += 1
                continue

            if DRY_RUN:
                print(f"[SIMULACIÓN] {source} -> {destination}")
            else:
                shutil.move(str(source), str(destination))
                print(f"[MOVIDO] {source.name} -> {destination}")

            moved += 1

    print("\n──── Resumen ────")
    print(f"Mosaicos seleccionados: {moved}")
    print(f"Archivos no encontrados: {missing}")
    print(f"Archivos omitidos: {skipped}")

    if DRY_RUN:
        print("\nSimulación terminada. Si todo está correcto,")
        print("cambia DRY_RUN = False para mover los archivos.")


if __name__ == "__main__":
    main()