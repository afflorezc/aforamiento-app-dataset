
import csv
import shutil
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────

REPORT_CSV = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/report.csv")

# Directorio donde están guardados los mosaicos generados.
# Debe coincidir con la ubicación de los archivos de la columna output.
MOSAICS_DIR = Path("mosaics")

# Directorio de destino para los mosaicos completos.
DEST_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics/completed")

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
            "prefix", "component", "tiles", "width", "height",
            "empty_pixels", "failed_pairs", "output"
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Faltan columnas en el CSV: "
                f"{required_columns - set(reader.fieldnames or [])}"
            )

        for row in reader:
            # Ignorar valores vacíos o no numéricos.
            try:
                empty_pixels = int(row["empty_pixels"].strip())
            except (ValueError, AttributeError):
                print(f"[AVISO] empty_pixels inválido: {row}")
                skipped += 1
                continue

            # Solo seleccionar mosaicos sin píxeles vacíos.
            if empty_pixels != 0:
                continue

            output_value = (row["output"] or "").strip()

            if not output_value:
                print(f"[AVISO] Sin ruta de salida: {row['prefix']}")
                missing += 1
                continue

            output_path = Path(output_value)

            # Si la ruta del CSV es relativa, intentar localizar
            # el archivo dentro de MOSAICS_DIR.
            if not output_path.is_absolute():
                candidates = [
                    output_path,
                    MOSAICS_DIR / output_path,
                    MOSAICS_DIR / output_path.name,
                ]
                source = next(
                    (p for p in candidates if p.is_file()),
                    None
                )
            else:
                source = output_path if output_path.is_file() else None

            if source is None:
                print(f"[NO ENCONTRADO] {output_value}")
                missing += 1
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