
import csv
import shutil
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────

REPORT_CSV = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates.csv")

CANDIDATES_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates")

VISIBLE_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates/visible")
NOT_VISIBLE_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/candidates/not_visible")
# Si es True, solo muestra los archivos que movería.
# Cambia a False para ejecutar los movimientos.
DRY_RUN = False

def main():
    VISIBLE_DIR.mkdir(parents=True, exist_ok=True)
    NOT_VISIBLE_DIR.mkdir(parents=True, exist_ok=True)

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

            filename = (row["filename"] or "").strip()

            source = Path(filename)
            source = CANDIDATES_DIR / source

            source = source if source.is_file() else None

            if source is None:
                print(f"[AVISO] el archivo {filename} no existe")
                missing += 1
                continue

            visible = (row["plants"] or "").strip()

            if visible == "":
                print(f"[AVISO] No hay información de visibilidad para {filename}")
                skipped += 1
                continue

            destination = "visible" if visible == "TRUE" else "not_visible"
            destination = Path(destination)
            destination = CANDIDATES_DIR / destination / source.name
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