#!/usr/bin/env python3
"""
Green Coffee Bean Defect Detection — YOLOv8 Training Script
=============================================================
Khusus untuk MacBook M2 (Apple Silicon) menggunakan MPS backend.

Dataset: Roboflow Green Coffee Bean Defects (16 classes)

Penggunaan:
    python training/train.py --data /path/to/data.yaml --epochs 100

Tips MacBook M2:
  - Gunakan device='mps' untuk akselerasi GPU lewat Metal
  - Batch 8-16 untuk M2 8GB RAM, 16-32 untuk M2 Pro/Max
  - workers=0 atau 2 — multiprocessing kadang bermasalah di Mac
  - Tutup aplikasi berat (Chrome, Docker) untuk free memory unified
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path


def cek_dependencies():
    """Pastikan semua paket yang dibutuhkan terinstall."""
    print("🔍 Cek dependencies...\n")
    missing = []

    try:
        import ultralytics
        print(f"   ✅ ultralytics    : {ultralytics.__version__}")
    except ImportError:
        missing.append("ultralytics")

    try:
        import torch
        print(f"   ✅ pytorch        : {torch.__version__}")
        if torch.backends.mps.is_available():
            print(f"   🚀 MPS available  : YES (Apple Silicon GPU siap pakai)")
        elif torch.cuda.is_available():
            print(f"   🚀 CUDA available : YES ({torch.cuda.get_device_name(0)})")
        else:
            print(f"   ⚠️  Hanya CPU yang tersedia — training akan lambat")
    except ImportError:
        missing.append("torch")

    try:
        import cv2
        print(f"   ✅ opencv         : {cv2.__version__}")
    except ImportError:
        missing.append("opencv-python")

    if missing:
        print(f"\n❌ Paket hilang: {', '.join(missing)}")
        print(f"   Install dengan: pip install {' '.join(missing)}")
        sys.exit(1)
    print()


def pilih_device(requested: str) -> str:
    """Pilih device terbaik. 'auto' → mps > cuda > cpu."""
    import torch

    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def validasi_dataset(data_yaml: Path):
    """Verifikasi struktur dataset & isi data.yaml."""
    import yaml

    if not data_yaml.exists():
        print(f"❌ data.yaml tidak ditemukan di: {data_yaml}")
        sys.exit(1)

    print(f"📂 Validasi dataset: {data_yaml}\n")
    with open(data_yaml, "r") as f:
        cfg = yaml.safe_load(f)

    # Field wajib
    for field in ["path", "train", "val", "nc", "names"]:
        if field not in cfg:
            print(f"   ❌ Field '{field}' hilang di data.yaml")
            sys.exit(1)

    base = Path(cfg["path"])
    train_dir = base / cfg["train"]
    val_dir = base / cfg["val"]

    if not train_dir.exists():
        print(f"   ❌ Train images tidak ada: {train_dir}")
        sys.exit(1)
    if not val_dir.exists():
        print(f"   ❌ Val images tidak ada: {val_dir}")
        sys.exit(1)

    n_train = len(list(train_dir.glob("*")))
    n_val = len(list(val_dir.glob("*")))

    print(f"   ✅ Train images   : {n_train}")
    print(f"   ✅ Val images     : {n_val}")
    print(f"   ✅ Classes        : {cfg['nc']}")
    names = cfg["names"]
    if isinstance(names, dict):
        names = list(names.values())
    print(f"   📋 Class names    : {names}\n")

    if n_train < 50:
        print("   ⚠️  Jumlah training image sangat sedikit. Pertimbangkan augmentasi.\n")

    return cfg


def latih(args):
    """Jalankan training YOLOv8."""
    from ultralytics import YOLO

    device = pilih_device(args.device)

    print("=" * 64)
    print("  GREEN BEAN DEFECT DETECTION — YOLOV8 TRAINING")
    print("=" * 64)
    print(f"  📅 Mulai      : {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  🖥️  Device     : {device.upper()}")
    print(f"  📊 Model      : {args.model}")
    print(f"  📁 Dataset    : {args.data}")
    print(f"  🔄 Epochs     : {args.epochs}")
    print(f"  📦 Batch      : {args.batch}")
    print(f"  📐 Image size : {args.imgsz}")
    print(f"  📂 Output     : {args.project}/{args.name}")
    print("=" * 64 + "\n")

    # Load model
    print("📥 Loading model...")
    model = YOLO(args.model)
    print(f"   Loaded: {args.model}\n")

    # =========================================================================
    # Augmentasi diperkuat untuk simulasi objek kecil & padat
    # =========================================================================
    train_args = dict(
        data=str(args.data),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        verbose=True,
        seed=42,
        patience=args.patience,
        save=True,
        save_period=10,
        cache=False,
        amp=device != "cpu",
        plots=True,

        # Warna (HSV) – variasikan warna biji
        hsv_h=0.02,
        hsv_s=0.8,
        hsv_v=0.5,

        # Rotasi & pergeseran
        degrees=15.0,
        translate=0.2,

        # Skala: 0.3–1.3x → mensimulasikan biji kecil (mis. 0.3x) hingga besar
        scale=0.3,

        # Shear / kemiringan
        shear=5.0,

        # Perspective – distorsi perspektif ringan
        perspective=0.0005,

        # Flip horizontal (kiri-kanan)
        fliplr=0.5,

        # Mosaic – gabungkan 4 gambar
        mosaic=1.0,

        # MixUp – overlap dua gambar
        mixup=0.2,

        # Copy-Paste – paste objek dari gambar lain (perlu Ultralytics ≥ 8.3)
        copy_paste=0.1,
    )

    # Optimasi khusus CPU
    if device == "cpu":
        train_args["workers"] = min(args.workers, 4)
        train_args["batch"] = min(args.batch, 8)
        print("⚡ CPU mode — settings dioptimasi.\n")

    # Optimasi khusus MPS (MacBook M-series)
    if device == "mps":
        train_args["workers"] = min(args.workers, 4)
        print("🍎 MPS mode (Apple Silicon) — workers dibatasi ke 4.\n")

    print("🚀 Memulai training...\n")
    try:
        model.train(**train_args)
    except KeyboardInterrupt:
        print("\n⚠️  Training dihentikan oleh user. Hasil parsial tersimpan.")
        return

    # Output
    out_dir = Path(args.project) / args.name
    best = out_dir / "weights" / "best.pt"
    last = out_dir / "weights" / "last.pt"

    print("\n" + "=" * 64)
    print("  ✅ TRAINING SELESAI!")
    print("=" * 64)
    print(f"  📂 Output    : {out_dir}")
    print(f"  🏆 Best      : {best}")
    print(f"  📄 Last      : {last}")
    if best.exists():
        size_mb = best.stat().st_size / (1024 * 1024)
        print(f"     Ukuran    : {size_mb:.2f} MB")
    print("=" * 64)
    print("\n📋 Langkah selanjutnya:")
    print(f"  1. Salin model ke backend:")
    print(f"     cp {best} backend/weights/best.pt")
    print(f"  2. Reload model di backend:")
    print(f"     curl -X POST http://localhost:8000/api/analyze/reload-model")
    print(f"  3. (Opsional) Validasi:")
    print(f"     yolo detect val model={best} data={args.data}\n")


def main():
    parser = argparse.ArgumentParser(
        description="YOLOv8 training untuk green coffee bean defect detection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:

  # Training di MacBook M2 (auto pilih MPS)
  python training/train.py --data ~/datasets/green-bean/data.yaml \\
      --epochs 100 --batch 16

  # Training force CPU (kalau MPS bermasalah)
  python training/train.py --data data.yaml --device cpu --batch 8

  # Resume dari checkpoint
  python training/train.py --data data.yaml \\
      --model runs/detect/green_bean/weights/last.pt
""",
    )

    parser.add_argument("--data", type=Path, required=True,
                        help="Path ke data.yaml")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        choices=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt",
                                 "yolov8l.pt", "yolov8x.pt"],
                        help="Varian YOLOv8 (default: yolov8n.pt — paling ringan)")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (kurangi jika OOM)")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cpu", "mps", "cuda", "0", "1"],
                        help="Device — 'mps' untuk MacBook M-series")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--patience", type=int, default=30,
                        help="Early stopping patience (epoch tanpa improvement)")
    parser.add_argument("--project", type=str, default="runs/detect")
    parser.add_argument("--name", type=str, default="green_bean")

    args = parser.parse_args()

    cek_dependencies()
    validasi_dataset(args.data)
    latih(args)


if __name__ == "__main__":
    main()