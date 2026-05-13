#!/usr/bin/env python3
"""
Menggabungkan greenbeans + greenbeans-terang ke dataset merged.
Asumsi: folder greenbeans dan greenbeans-terang sudah ada di datasets/.
"""
import shutil
from pathlib import Path

BASE = Path("datasets")
MERGED = BASE / "merged-dataset"
JIMMY = BASE / "green-bean-defects"

# Kelas greenbeans (urutan dari Roboflow)
GB_CLASSES = [
    "Benda asing", "Biji berkulit tanduk", "Biji berlubang",
    "Biji bertutul-tutul", "Biji coklat", "Biji hitam",
    "Biji hitam pecah", "Biji hitam sebagian", "Biji normal",
    "Biji pecah", "Kopi gelondong", "Kulit kopi", "Kulit tanduk"
]

# Mapping greenbeans -> nama Jimmy (16 kelas)
GB_TO_JIMMY = {
    "Benda asing": None,
    "Biji berkulit tanduk": "parchment",
    "Biji berlubang": "immature",
    "Biji bertutul-tutul": "fungus",
    "Biji coklat": "partial_sour",
    "Biji hitam": "full_black",
    "Biji hitam pecah": "broken",
    "Biji hitam sebagian": "partial_black",
    "Biji normal": None,
    "Biji pecah": "broken",
    "Kopi gelondong": "dry_cherry",
    "Kulit kopi": "husk",
    "Kulit tanduk": "parchment",
}

JIMMY_NAMES = [
    "broken", "cut", "dry_cherry", "fade", "floater",
    "full_black", "full_sour", "fungus", "husk", "immature",
    "parchment", "partial_black", "partial_sour",
    "severe_insect_damage", "shell", "withered"
]
NAME_TO_IDX = {name: i for i, name in enumerate(JIMMY_NAMES)}

def process_folder(gb_path, split):
    img_src = gb_path / split / "images"
    lbl_src = gb_path / split / "labels"
    if not img_src.exists() or not lbl_src.exists():
        return 0

    count = 0
    for img_file in img_src.glob("*"):
        lbl_file = lbl_src / (img_file.stem + ".txt")
        if not lbl_file.exists():
            continue

        new_lines = []
        with open(lbl_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                old_cls = int(parts[0])
                if old_cls >= len(GB_CLASSES):
                    continue
                cls_name = GB_CLASSES[old_cls]
                jimmy_name = GB_TO_JIMMY.get(cls_name)
                if jimmy_name is None:
                    continue  # buang benda asing & normal
                new_cls = NAME_TO_IDX[jimmy_name]
                parts[0] = str(new_cls)
                new_lines.append(" ".join(parts))

        if not new_lines:
            continue

        dest_img = MERGED / split / "images" / img_file.name
        shutil.copy(img_file, dest_img)

        dest_lbl = MERGED / split / "labels" / lbl_file.name
        with open(dest_lbl, "w") as f:
            f.write("\n".join(new_lines))
        count += 1
    return count

# Buat struktur merged
for split in ["train", "valid"]:
    (MERGED / split / "images").mkdir(parents=True, exist_ok=True)
    (MERGED / split / "labels").mkdir(parents=True, exist_ok=True)

# Salin dataset Jimmy
print("📋 Menyalin dataset Jimmy...")
for split in ["train", "valid"]:
    for ext in ["images", "labels"]:
        src = JIMMY / split / ext
        dst = MERGED / split / ext
        if src.exists():
            for f in src.glob("*"):
                shutil.copy(f, dst)

# Proses greenbeans
for gb_name in ["greenbeans", "greenbeans-terang"]:
    gb_path = BASE / gb_name
    if not gb_path.exists():
        print(f"⚠️  {gb_path} tidak ditemukan, lewati.")
        continue
    print(f"🔄 Memproses {gb_name}...")
    for split in ["train", "valid"]:
        n = process_folder(gb_path, split)
        print(f"   {split}: {n} gambar ditambahkan")

print("✅ Selesai! Dataset merged ada di:", MERGED.resolve())