"""
Pelatihan YOLOv8 untuk deteksi defect green coffee bean (9 kelas SCA Inggris).

Dataset gabungan: datasets/merged (coffee-bean-defect.v3i + green-coffee-bean-defect.v1i).
Kelas: black, broken, foreign, fraghusk, green, husk, immature, infested, sour.

Pemakaian:
    # Pelatihan penuh (produksi)
    python train_coffee.py --epochs 100 --imgsz 640 --model yolov8n.pt

    # Smoke test cepat (verifikasi pipeline, subset kecil)
    python train_coffee.py --smoke

Setelah selesai, salin bobot terbaik ke backend lalu reload:
    cp runs/detect/<run>/weights/best.pt ../backend/weights/best.pt
    curl -X POST http://localhost:8000/api/v1/analyze/reload-model
"""
import argparse
from pathlib import Path

from ultralytics import YOLO


HERE = Path(__file__).resolve().parent
DATA_YAML = HERE.parent / "datasets" / "merged" / "data.yaml"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolov8n.pt", help="model dasar / checkpoint")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default=None, help="'mps' | 'cpu' | '0' (cuda). Default auto.")
    ap.add_argument("--cache", default=None, choices=["ram", "disk"],
                    help="Cache gambar untuk mempercepat ('disk' aman, 'ram' tercepat)")
    ap.add_argument("--smoke", action="store_true",
                    help="Uji cepat: 1 epoch, 5% data, imgsz 320")
    args = ap.parse_args()

    if not DATA_YAML.exists():
        raise SystemExit(
            f"data.yaml tidak ditemukan di {DATA_YAML}. "
            "Jalankan datasets/merge_datasets.py dulu."
        )

    kwargs = dict(
        data=str(DATA_YAML),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=20,
        project=str(HERE / "runs"),
    )
    if args.device:
        kwargs["device"] = args.device
    if args.cache:
        kwargs["cache"] = args.cache
    if args.smoke:
        kwargs.update(epochs=1, imgsz=320, fraction=0.05, name="smoke")

    model = YOLO(args.model)
    model.train(**kwargs)
    print("✓ Pelatihan selesai. Bobot terbaik ada di runs/detect/<run>/weights/best.pt")


if __name__ == "__main__":
    main()
