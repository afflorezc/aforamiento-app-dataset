
from pathlib import Path
from collections import defaultdict, deque
from itertools import combinations
import re
import csv

import cv2
import numpy as np
from PIL import Image


# ==================================================
# CONFIGURACION
# ==================================================

INPUT_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-zenodo")
OUTPUT_DIR = Path("/home/andres/Documents/Proyecto integrador/datasets/ds-mosaics")

EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

PATTERN = re.compile(
    r"^(?P<prefix>.+)_r(?P<row>\d+)_c(?P<col>\d+)$",
    re.IGNORECASE,
)

# Minimo de correspondencias geometricamente coherentes.
MIN_INLIERS = 8

# ORB puede detectar hasta este numero de puntos por imagen.
MAX_FEATURES = 5000


# ==================================================
# 1. AGRUPAR TILES SIN DISTINGUIR EL SPLIT
# ==================================================

def discover_tiles(root):
    groups = defaultdict(dict)
    unmatched = []
    duplicates = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in EXTENSIONS:
            continue

        match = PATTERN.match(path.stem)

        if not match:
            unmatched.append(str(path))
            continue

        prefix = match.group("prefix")
        row = int(match.group("row"))
        col = int(match.group("col"))

        # Deliberadamente NO se incluye train/val/test.
        key = prefix
        coord = (row, col)

        if coord in groups[key]:
            duplicates.append(
                (key, coord, str(path), str(groups[key][coord]))
            )
            continue

        groups[key][coord] = path

    return groups, unmatched, duplicates


# ==================================================
# 2. ESTIMAR DESPLAZAMIENTO ENTRE DOS TILES
# ==================================================

def estimate_translation(path_a, path_b, direction):
    """
    Estima el desplazamiento de B respecto a A.

    direction:
        "horizontal": B debe estar a la derecha de A.
        "vertical":   B debe estar debajo de A.

    Devuelve (dx, dy, inliers), o None si falla.
    """

    image_a = cv2.imread(str(path_a), cv2.IMREAD_GRAYSCALE)
    image_b = cv2.imread(str(path_b), cv2.IMREAD_GRAYSCALE)

    if image_a is None or image_b is None:
        return None

    if image_a.shape != image_b.shape:
        print(f"[ERROR] Dimensiones incompatibles: {path_a}, {path_b}")
        return None

    orb = cv2.ORB_create(nfeatures=MAX_FEATURES)

    kp_a, des_a = orb.detectAndCompute(image_a, None)
    kp_b, des_b = orb.detectAndCompute(image_b, None)

    if des_a is None or des_b is None:
        return None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(des_a, des_b, k=2)

    good = [
        m for pair in pairs
        if len(pair) == 2
        for m, n in [pair]
        if m.distance < 0.75 * n.distance
    ]

    if len(good) < MIN_INLIERS:
        return None

    points_a = np.float32([
        kp_a[m.queryIdx].pt for m in good
    ])

    points_b = np.float32([
        kp_b[m.trainIdx].pt for m in good
    ])

    # Transformacion de puntos de A a coordenadas de B.
    # Para tiles de una misma imagen se espera principalmente
    # una traslacion, sin rotacion ni cambio de escala.
    matrix, mask = cv2.estimateAffinePartial2D(
        points_a,
        points_b,
        method=cv2.RANSAC,
        ransacReprojThreshold=3.0,
        maxIters=3000,
        confidence=0.99,
    )

    if matrix is None or mask is None:
        return None

    inliers = int(mask.sum())

    if inliers < MIN_INLIERS:
        return None

    # Rechazar rotaciones o escalas significativas.
    linear = matrix[:, :2]
    scale = np.sqrt(np.linalg.det(linear))

    if scale <= 0 or abs(scale - 1.0) > 0.03:
        return None

    rotation = np.degrees(
        np.arctan2(matrix[1, 0], matrix[0, 0])
    )

    if abs(rotation) > 2.0:
        return None

    # El modelo estima A -> B.
    # La posicion global de B es pos(A) - traslacion.
    tx, ty = matrix[:, 2]
    dx, dy = -float(tx), -float(ty)

    # Validar el sentido del desplazamiento.
    if direction == "horizontal":
        if dx <= 0:
            return None
    else:
        if dy <= 0:
            return None

    return dx, dy, inliers


# ==================================================
# 3. CREAR GRAFO DE VECINOS
# ==================================================

def build_graph(tiles):
    """
    Cada tile se conecta con su vecino derecho y su vecino inferior.
    Las aristas contienen el desplazamiento estimado.
    """

    graph = defaultdict(list)
    failed = []

    for row, col in sorted(tiles):
        a = (row, col)

        for b, direction in [
            ((row, col + 1), "horizontal"),
            ((row + 1, col), "vertical"),
        ]:
            if b not in tiles:
                continue

            result = estimate_translation(
                tiles[a], tiles[b], direction
            )

            if result is None:
                failed.append((a, b))
                continue

            dx, dy, inliers = result

            # Posicion de B respecto a A.
            graph[a].append((b, dx, dy, inliers))
            graph[b].append((a, -dx, -dy, inliers))

            print(
                f"[ALINEADO] {a} -> {b} | "
                f"dx={dx:.1f}, dy={dy:.1f}, "
                f"correspondencias={inliers}"
            )

    return graph, failed


# ==================================================
# 4. CALCULAR POSICIONES GLOBALES
# ==================================================

def calculate_positions(tiles, graph):
    """
    Propaga las posiciones desde un tile de referencia.
    Cada componente desconectado recibe su propio origen.
    """

    positions = {}
    components = []

    for start in sorted(tiles):
        if start in positions:
            continue

        positions[start] = (0.0, 0.0)
        component = []
        queue = deque([start])

        while queue:
            current = queue.popleft()
            component.append(current)

            x, y = positions[current]

            for neighbor, dx, dy, _ in graph[current]:
                proposed = (x + dx, y + dy)

                if neighbor not in positions:
                    positions[neighbor] = proposed
                    queue.append(neighbor)

        components.append(component)

    return positions, components


# ==================================================
# 5. FUSIONAR LOS TILES
# ==================================================

def render_component(tiles, positions, component, output_path):
    """
    Crea el mosaico usando promedio de pixeles en las zonas
    superpuestas. Las posiciones se redondean a pixeles.
    """

    images = {}
    coords = {}

    for tile in component:
        image = cv2.imread(str(tiles[tile]), cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError(f"No se pudo leer {tiles[tile]}")

        x, y = positions[tile]
        coords[tile] = (round(x), round(y))
        images[tile] = image

    shapes = {im.shape[:2] for im in images.values()}

    if len(shapes) != 1:
        raise ValueError(
            "Los tiles tienen dimensiones diferentes."
        )

    height, width = next(iter(shapes))

    min_x = min(x for x, y in coords.values())
    min_y = min(y for x, y in coords.values())

    # Desplazar todo para que el origen sea positivo.
    for tile, (x, y) in list(coords.items()):
        coords[tile] = (x - min_x, y - min_y)

    max_x = max(x + width for x, y in coords.values())
    max_y = max(y + height for x, y in coords.values())

    # Acumuladores para promediar las zonas solapadas.
    accumulator = np.zeros(
        (max_y, max_x, 3), dtype=np.float32
    )
    weights = np.zeros((max_y, max_x), dtype=np.float32)

    for tile, image in images.items():
        x, y = coords[tile]

        accumulator[y:y + height, x:x + width] += (
            image.astype(np.float32)
        )
        weights[y:y + height, x:x + width] += 1.0

    # Si hay huecos reales, se mantienen negros y se notifican.
    missing_pixels = int(np.count_nonzero(weights == 0))

    valid = weights > 0
    output = np.zeros_like(accumulator)

    output[valid] = (
        accumulator[valid] / weights[valid, None]
    )

    output = np.clip(output, 0, 255).astype(np.uint8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), output)

    return {
        "tiles": len(component),
        "width": max_x,
        "height": max_y,
        "empty_pixels": missing_pixels,
        "output": str(output_path),
    }


# ==================================================
# 6. EJECUCION
# ==================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    groups, unmatched, duplicates = discover_tiles(INPUT_DIR)

    print(f"Grupos por prefijo: {len(groups)}")
    print(f"Imagenes sin patron r/c: {len(unmatched)}")
    print(f"Coordenadas duplicadas: {len(duplicates)}")

    report = []

    for prefix, tiles in sorted(groups.items()):
        print(f"\n===== {prefix} ({len(tiles)} tiles) =====")

        graph, failed = build_graph(tiles)
        positions, components = calculate_positions(tiles, graph)

        if failed:
            print(f"[AVISO] Parejas sin alinear: {len(failed)}")

        if len(components) > 1:
            print(
                f"[AVISO] {len(components)} componentes "
                "desconectados; no se puede garantizar "
                "un unico mosaico continuo."
            )

        for index, component in enumerate(components, start=1):
            # Nombre seguro y unico por componente.
            safe_prefix = re.sub(
                r"[^A-Za-z0-9_.-]+", "_", prefix
            )

            name = f"{safe_prefix}_part{index:02d}.jpg"
            output_path = OUTPUT_DIR / name

            try:
                result = render_component(
                    tiles, positions, component, output_path
                )
            except Exception as error:
                print(f"[ERROR] {prefix}: {error}")
                continue

            result.update({
                "prefix": prefix,
                "component": index,
                "failed_pairs": len(failed),
            })

            report.append(result)

            print(
                f"[GUARDADO] {output_path} | "
                f"{result['width']}x{result['height']} | "
                f"pixeles vacios: {result['empty_pixels']}"
            )

    report_path = OUTPUT_DIR / "report.csv"

    with report_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        fields = [
            "prefix", "component", "tiles",
            "width", "height", "empty_pixels",
            "failed_pairs", "output"
        ]

        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report)

    print("\n========== RESUMEN ==========")
    print(f"Grupos originales: {len(groups)}")
    print(f"Componentes generados: {len(report)}")
    print(f"Informe: {report_path}")


if __name__ == "__main__":
    main()