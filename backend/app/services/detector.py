"""
Service deteksi defect green coffee bean menggunakan YOLOv8.

Mendukung device:
  - 'mps'  : Apple Silicon (MacBook M1/M2/M3) via Metal Performance Shaders
  - 'cuda' : GPU NVIDIA
  - 'cpu'  : Fallback
  - 'auto' : Pilih otomatis berdasarkan ketersediaan
"""
import time
import uuid
from pathlib import Path
from typing import Tuple, Dict, List

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from app.config import settings


# Class names dari dataset Roboflow (18 kelas defect)
CLASS_NAMES = [
    "broken",
    "cut",
    "dry_cherry",
    "fade",
    "floater",
    "full_black",
    "full_sour",
    "fungus",
    "husk",
    "immature",
    "insect_damaged",
    "parchment",
    "partial_black",
    "partial_sour",
    "severe_insect_damage",
    "shell",
    "slight_insect_damage",
    "withered",
]


def _resolve_device(requested: str) -> str:
    """Pilih device terbaik berdasarkan ketersediaan hardware."""
    if requested == "auto":
        if torch.backends.mps.is_available():
            return "mps"  # MacBook M1/M2/M3
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return requested


class BeanDetector:
    """
    Detector singleton untuk YOLO green bean defect.

    Usage:
        detector = BeanDetector()
        result = detector.detect("path/to/image.jpg")
    """

    _instance = None

    def __new__(cls):
        # Singleton supaya model hanya di-load sekali
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.device = _resolve_device(settings.DEVICE)
        self.model_path = settings.model_full_path
        self.model = None

        # Load model jika file ada
        if self.model_path.exists():
            self._load_model()
        else:
            print(
                f"⚠️  Model tidak ditemukan di {self.model_path}\n"
                f"   Endpoint /api/analyze akan gagal sampai model dilatih."
            )

        self._initialized = True

    def _load_model(self):
        """Load YOLO model ke memory."""
        print(f"📥 Loading YOLO model dari {self.model_path}")
        print(f"   Device: {self.device}")
        self.model = YOLO(str(self.model_path))

        # Warm up model (forward pass kosong) supaya request pertama tidak lambat
        try:
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(
                dummy, device=self.device, verbose=False, imgsz=640
            )
            print("   Model siap digunakan!")
        except Exception as exc:
            print(f"   Warm-up gagal (tidak fatal): {exc}")

    def is_ready(self) -> bool:
        return self.model is not None

    def reload(self):
        """Reload model — dipakai kalau weights di-update tanpa restart."""
        if self.model_path.exists():
            self._load_model()

    def detect(
        self,
        image_path: str,
        save_result: bool = True,
    ) -> Tuple[Dict, str, int]:
        """
        Jalankan deteksi pada satu gambar.

        Returns:
            (result_dict, result_image_path, processing_time_ms)
        """
        if not self.is_ready():
            raise RuntimeError(
                "Model belum di-load. Pastikan file weights/best.pt tersedia."
            )

        start = time.time()

        # Inference
        results = self.model.predict(
            source=image_path,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            device=self.device,
            verbose=False,
            imgsz=640,
        )

        result = results[0]
        boxes = result.boxes

        # Parse hasil
        detections: List[Dict] = []
        class_counts: Dict[str, int] = {}
        confidences = []

        if boxes is not None and len(boxes) > 0:
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                conf = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].cpu().numpy().tolist()

                # Gunakan nama dari model jika tersedia, fallback ke CLASS_NAMES
                if hasattr(self.model, "names") and cls_id in self.model.names:
                    cls_name = self.model.names[cls_id]
                elif cls_id < len(CLASS_NAMES):
                    cls_name = CLASS_NAMES[cls_id]
                else:
                    cls_name = f"class_{cls_id}"

                detections.append(
                    {
                        "class_name": cls_name,
                        "confidence": round(conf, 4),
                        "bbox": [round(v, 2) for v in xyxy],
                    }
                )
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                confidences.append(conf)

        # Simpan gambar dengan bounding box
        result_image_path = ""
        if save_result:
            result_image_path = self._save_annotated(result, image_path)

        elapsed_ms = int((time.time() - start) * 1000)

        return (
            {
                "total_defects": len(detections),
                "detections": detections,
                "class_counts": class_counts,
                "confidence_avg": (
                    round(sum(confidences) / len(confidences), 4)
                    if confidences
                    else 0.0
                ),
            },
            result_image_path,
            elapsed_ms,
        )

    def _save_annotated(self, result, original_path: str) -> str:
        """Simpan gambar dengan bbox tergambar di folder uploads/."""
        annotated = result.plot()  # numpy BGR
        out_name = f"result_{uuid.uuid4().hex[:8]}_{Path(original_path).name}"
        out_path = settings.upload_full_path / out_name
        cv2.imwrite(str(out_path), annotated)
        return str(out_path)


# ==================================================
# GRADING LOGIC (SCA-style simplified)
# ==================================================
def calculate_grade(
    total_defects: int, weight_gram: float
) -> Tuple[str, float]:
    """
    Hitung grade berdasarkan jumlah defect per 350 gram.

    Standar SCA disederhanakan:
        Grade 1 (Specialty)     : 0-5  defect
        Grade 2 (Premium)       : 6-8  defect
        Grade 3 (Exchange)      : 9-23 defect
        Grade 4 (Below Standard): >23  defect

    Args:
        total_defects : jumlah defect yang terdeteksi pada gambar
        weight_gram   : berat sampel sebenarnya (gram)

    Returns:
        (grade_code, defects_per_350g)
    """
    # Normalisasi defect ke per 350g (standar SCA)
    if weight_gram <= 0:
        weight_gram = 350.0
    defects_per_350g = (total_defects / weight_gram) * 350.0

    if defects_per_350g <= 5:
        return "GRADE_1", round(defects_per_350g, 2)
    if defects_per_350g <= 8:
        return "GRADE_2", round(defects_per_350g, 2)
    if defects_per_350g <= 23:
        return "GRADE_3", round(defects_per_350g, 2)
    return "GRADE_4", round(defects_per_350g, 2)