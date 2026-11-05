
import csv
import shutil
from pathlib import Path
import re

# ── Configuración ─────────────────────────────────────────────

REPORT_CSV = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-zenodo/tile_analysis/mosaic_summary.csv")

# Directorio donde están guardados los mosaicos generados.
# Debe coincidir con la ubicación de los archivos de la columna output.
MOSAICS_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics")

EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

PATTERN = re.compile(
    r"^(?P<prefix>.+)_part(?P<part>\d+)$",
    re.IGNORECASE,
)

# Si es True, solo muestra los archivos que movería.
# Cambia a False para ejecutar los movimientos.
DRY_RUN = False

def main():

    moved = 0
    missing = 0
    skipped = 0

    with REPORT_CSV.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        required_columns = {
            "split", "versions_found", "prefix", "tiles_found", "rows_span", "cols_span",
            "grid_positions", "missing_positions", "image_dimensions", "missing_coordinates"
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Faltan columnas en el CSV: "
                f"{required_columns - set(reader.fieldnames or [])}"
            )

        for row in reader:
            # Ignorar valores vacíos o no numéricos.
            try:
                missing_positions = int(row["missing_positions"].strip())
            except (ValueError, AttributeError):
                print(f"[AVISO] missing_positions inválido: {row}")
                skipped += 1
                continue

            prefix = (row["prefix"] or "").strip()

            if not prefix:
                print(f"[AVISO] Sin Prefix: {row['prefix']}")
                missing += 1
                continue
            
            dirname = f"missing_{missing_positions}"
            dirname = Path(dirname)
            
            out_dir = MOSAICS_DIR / dirname

            if not DRY_RUN:
                out_dir.mkdir(parents=True, exist_ok=True)

            for path in MOSAICS_DIR.iterdir():
                if not path.is_file():
                    continue
                
                if path.suffix.lower() not in EXTENSIONS:
                    continue

                match = PATTERN.match(path.stem)
                
                if not match:
                    continue
                
                if match.group("prefix") == prefix:
                    print(f"Mached prefix: {prefix}")
                    source = path 
                    destination = out_dir / source.name
                    print(f"Destination: {destination}")

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