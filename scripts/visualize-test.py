
from __future__ import annotations
from pathlib import Path
import argparse
import os
import cv2

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
LABEL_EXT = (".txt",)

def visualize_labels(img, label, output_dir):
    image = cv2.imread(str(img))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = image.shape[:2]

    with open(str(label)) as file:
        for line in file:
            class_id, xc, yc, bw, bh = map(
                float, line.split()
            )

            x1 = int((xc - bw / 2) * width)
            y1 = int((yc - bh / 2) * height)
            x2 = int((xc + bw / 2) * width)
            y2 = int((yc + bh / 2) * height)

            cv2.rectangle(
                image, (x1, y1), (x2, y2),
                (0, 0, 255), 4
            )

            cv2.putText(
                image, f"{int(class_id)}",
                (x1, max(y1 - 5, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 0, 255), 1
            )
    
    img_name = img.name
    out_image = output_dir / img_name
    try:
        cv2.imwrite(out_image, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    except IOError:
        print(f"No se pudo agregar etiquetas a {img_name}")


def identify_yolo(src_dir):
    # Identifies the YOLO  folder structure of the src_dir dataset
    splits = {}
    
    # pattern: src_dir/images/train, src_dir/labels/train
    for split in ("train", "val", "valid", "test"):
        img = src_dir / "images" / split
        lbl = src_dir / "labels" / split
        if img.is_dir() and lbl.is_dir():
            splits[split] = (img, lbl)
    if splits:
        return splits
    
    # pattern: src_dir/train/images, src_/train/labels
    for split in ("train", "val", "valid", "test"):
        img = src_dir / split / "images"
        lbl = src_dir / split / "labels"
        if img.is_dir() and lbl.is_dir():
            splits[split] = (img, lbl)
    if splits:
        return splits

    # pattern: src_dir/train, src_dir/test, src_dir/valid
    for split in ("train", "val", "valid", "test"):
        img_lbl = src_dir / split
        if img_lbl.is_dir():
            splits[split] = (img_lbl, img_lbl)
    return splits

def process_dataset(src_dir, out_dir):
    splits = identify_yolo(src_dir)

    for split, dirs in splits.items():
        output_dir = out_dir / split
        os.makedirs(output_dir, exist_ok=True)
        img_dir = dirs[0]
        labels_dir = dirs[1]

        for image in img_dir.glob("*"):
            if not image.is_file():
                continue
            
            if not image.suffix in IMG_EXT:
                continue
            
            label_name = f"{image.stem}.txt"
            label_path = labels_dir / label_name
            if not label_path.is_file():
                continue
            
            visualize_labels(image, label_path, output_dir)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Directorio de dataset")
    ap.add_argument("--out", default="labelled-dataset")
    args = ap.parse_args()

    dataset_dir = Path(args.dir)
    
    if not os.path.isdir(dataset_dir):
        raise SystemExit(
            f"No se pudo encontrar la ruta ingresada: {dataset_dir}."
        )

    os.makedirs(args.out, exist_ok=True)
    output_dir = Path(args.out)
    process_dataset(dataset_dir, output_dir)

if __name__ == "__main__":
    main()
    
