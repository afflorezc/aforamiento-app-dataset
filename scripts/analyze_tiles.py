
from pathlib import Path
from collections import defaultdict
from PIL import Image
import pandas as pd
import re

# Cambia esta ruta por la carpeta raíz de tu dataset.
ROOT = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-zenodo")
OUTPUT = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-zenodo/tile_analysis")
OUTPUT.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# Ejemplo: 20250703_10-58_CLOUDY_004_r4_c1.jpg
PATTERN = re.compile(
    r"^(?P<prefix>.+)_r(?P<row>\d+)_c(?P<col>\d+)$",
    re.IGNORECASE,
)

groups = defaultdict(list)
unmatched = []
sizes = []

for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    match = PATTERN.match(path.stem)
    if not match:
        unmatched.append(str(path))
        continue

    # Identifica la partición y la versión del dataset.
    relative = path.relative_to(ROOT)
    parts = relative.parts

    version = next(
        (p for p in parts if p.lower() in {"ds-v1", "ds-v2"}),
        "unknown",
    )

    split = next(
        (p for p in parts if p.lower() in {"train", "val", "test"}),
        "unknown",
    )

    prefix = match.group("prefix")
    row = int(match.group("row"))
    col = int(match.group("col"))

    try:
        with Image.open(path) as im:
            width, height = im.size
    except Exception as exc:
        print(f"No se pudo leer {path}: {exc}")
        continue

    key = (split, prefix)

    groups[key].append({
        "path": str(path),
        "row": row,
        "col": col,
        "width": width,
        "height": height,
        "version": version,
    })

    sizes.append({
        "split": split,
        "version": version,
        "prefix": prefix,
        "file": path.name,
        "width": width,
        "height": height,
    })

summary = []
missing = []

for (split, prefix), tiles in groups.items():
    coordinates = {(t["row"], t["col"]) for t in tiles}

    min_row = min(r for r, c in coordinates)
    max_row = max(r for r, c in coordinates)
    min_col = min(c for r, c in coordinates)
    max_col = max(c for r, c in coordinates)

    expected = {
        (r, c)
        for r in range(min_row, max_row + 1)
        for c in range(min_col, max_col + 1)
    }

    absent = sorted(expected - coordinates)
    dimensions = {(t["width"], t["height"]) for t in tiles}

    summary.append({
        "split": split,
        "versions_found": ", ".join(
            sorted({t["version"] for t in tiles})
        ),
        "prefix": prefix,
        "tiles_found": len(tiles),
        "rows_span": max_row - min_row + 1,
        "cols_span": max_col - min_col + 1,
        "grid_positions": len(expected),
        "missing_positions": len(absent),
        "image_dimensions": str(sorted(dimensions)),
        "missing_coordinates": "; ".join(
            f"r{r}_c{c}" for r, c in absent
        ),
    })

    for r, c in absent:
        missing.append({
            "split": split,
            "version": version,
            "prefix": prefix,
            "missing_row": r,
            "missing_col": c,
        })

pd.DataFrame(summary).to_csv(
    OUTPUT / "mosaic_summary.csv", index=False
)
pd.DataFrame(missing).to_csv(
    OUTPUT / "missing_tiles.csv", index=False
)
pd.DataFrame(sizes).to_csv(
    OUTPUT / "tile_dimensions.csv", index=False
)

with open(OUTPUT / "unmatched_files.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(unmatched))

print(f"Vuelos/grupos analizados: {len(groups)}")
print(f"Posiciones faltantes detectadas: {len(missing)}")
print(f"Resultados guardados en: {OUTPUT.resolve()}")