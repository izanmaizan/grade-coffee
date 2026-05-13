"""
Service deteksi defect green coffee bean menggunakan YOLOv8.
Mendukung tiling inference (SAHI-style) untuk mendeteksi objek kecil
pada gambar bergram. Nama kelas otomatis dari model (bahasa Indonesia).
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


def _resolve_device(requested: str) -> str:
    if requested == "auto":
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return requested


class BeanDetector:
    """Detektor singleton YOLO untuk green bean defect."""

    _instance = None

    def __new__(cls):
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
        if self.model_path.exists():
            self._load_model()
        else:
            print(f"⚠️  Model tidak ditemukan di {self.model_path}")
        self._initialized = True

    def _load_model(self):
        """Muat model YOLO dan lakukan warm-up."""
        print(f"📥 Loading YOLO model dari {self.model_path}")
        print(f"   Device: {self.device}")
        self.model = YOLO(str(self.model_path))
        try:
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(dummy, device=self.device, verbose=False, imgsz=640)
            print("   Model siap digunakan!")
            # Tampilkan nama kelas yang dikenali
            print(f"   Kelas terdeteksi: {list(self.model.names.values()) if hasattr(self.model, 'names') else 'default'}")
        except Exception as e:
            print(f"   Warm-up gagal (tidak fatal): {e}")

    def is_ready(self) -> bool:
        return self.model is not None

    def reload(self):
        """Muat ulang model (setelah training baru)."""
        if self.model_path.exists():
            self._load_model()

    def detect(self, image_path: str, save_result: bool = True) -> Tuple[Dict, str, int]:
        """Deteksi objek pada gambar.

        Returns:
            (result_dict, result_image_path, processing_time_ms)
        """
        if not self.is_ready():
            raise RuntimeError("Model belum di-load.")

        start = time.time()

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Gambar tidak bisa dibaca.")

        # Baca konfigurasi dari environment
        tiling_enabled = getattr(settings, 'TILING_ENABLED', 'false').lower() == 'true'
        tile_size = int(getattr(settings, 'TILING_SIZE', '640'))
        tile_overlap = int(getattr(settings, 'TILING_OVERLAP', '100'))
        tta_enabled = getattr(settings, 'TTA_ENABLED', 'false').lower() == 'true'

        conf = settings.CONFIDENCE_THRESHOLD
        iou = settings.IOU_THRESHOLD

        all_detections: List[Dict] = []

        if tiling_enabled and (img.shape[0] > tile_size or img.shape[1] > tile_size):
            print(f"🧩 Tiling inference enabled: tile={tile_size}, overlap={tile_overlap}")
            tiles_info = self._slice_image(img, tile_size, tile_overlap)
            for (x1, y1, x2, y2), tile_img in tiles_info:
                dets = self._detect_on_array(tile_img, conf, iou, tta_enabled)
                # Kembalikan koordinat ke gambar asli
                for d in dets:
                    d['bbox'][0] += x1
                    d['bbox'][1] += y1
                    d['bbox'][2] += x1
                    d['bbox'][3] += y1
                all_detections.extend(dets)
            # Gabungkan kotak yang tumpang tindih dari berbagai tile
            all_detections = self._merge_detections(all_detections, iou)
        else:
            all_detections = self._detect_on_array(img, conf, iou, tta_enabled)

        elapsed_ms = int((time.time() - start) * 1000)

        # Ringkasan per kelas
        class_counts: Dict[str, int] = {}
        confidences = []
        for d in all_detections:
            cls_name = d['class_name']
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            confidences.append(d['confidence'])

        result_image_path = ""
        if save_result:
            result_image_path = self._save_annotated(img, all_detections, image_path)

        result = {
            "total_defects": len(all_detections),
            "detections": all_detections,
            "class_counts": class_counts,
            "confidence_avg": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        }
        return result, result_image_path, elapsed_ms

    def _detect_on_array(self, img: np.ndarray, conf: float, iou: float, tta: bool = False) -> List[Dict]:
        """Jalankan inferensi pada array gambar."""
        results = self.model.predict(
            source=img,
            conf=conf,
            iou=iou,
            device=self.device,
            verbose=False,
            imgsz=640,
            augment=tta,
        )
        result = results[0]
        boxes = result.boxes
        detections = []
        if boxes is not None and len(boxes) > 0:
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                conf_val = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].cpu().numpy().tolist()
                # Gunakan nama kelas dari model (sudah bahasa Indonesia)
                if hasattr(self.model, "names") and cls_id in self.model.names:
                    cls_name = self.model.names[cls_id]
                else:
                    cls_name = f"class_{cls_id}"
                detections.append({
                    "class_name": cls_name,
                    "confidence": round(conf_val, 4),
                    "bbox": [round(v, 2) for v in xyxy],
                })
        return detections

    def _slice_image(self, img: np.ndarray, size: int, overlap: int) -> List[Tuple[Tuple[int,int,int,int], np.ndarray]]:
        """Potong gambar menjadi grid tile."""
        h, w = img.shape[:2]
        tiles = []
        y = 0
        while y < h:
            x = 0
            while x < w:
                x2 = min(x + size, w)
                y2 = min(y + size, h)
                tile_img = img[y:y2, x:x2].copy()
                tiles.append(((x, y, x2, y2), tile_img))
                x += size - overlap
                if x2 >= w:
                    break
            y += size - overlap
            if y2 >= h:
                break
        return tiles

    def _merge_detections(self, detections: List[Dict], iou_thr: float) -> List[Dict]:
        """Gabungkan deteksi dari tile yang tumpang tindih."""
        if not detections:
            return detections
        boxes_list = [d['bbox'] for d in detections]
        scores = [d['confidence'] for d in detections]
        indices = cv2.dnn.NMSBoxes(boxes_list, scores, score_threshold=0.0, nms_threshold=iou_thr)
        if len(indices) == 0:
            return []
        merged = [detections[i] for i in indices.flatten().tolist()]
        return merged

    def _save_annotated(self, img: np.ndarray, detections: List[Dict], original_path: str) -> str:
        """Simpan gambar dengan bounding box berwarna."""
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det['class_name']} {det['confidence']:.2f}"
            cv2.putText(img, label, (x1, max(y1 - 10, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        out_name = f"result_{uuid.uuid4().hex[:8]}_{Path(original_path).name}"
        out_path = settings.upload_full_path / out_name
        cv2.imwrite(str(out_path), img)
        return str(out_path)


def calculate_grade(total_defects: int, weight_gram: float) -> Tuple[str, float]:
    """Hitung grade SCA berdasarkan jumlah defect per 350g."""
    if weight_gram <= 0:
        weight_gram = 350.0
    defects_per_350g = (total_defects / weight_gram) * 350.0

    if defects_per_350g <= 5:
        return "GRADE_1", round(defects_per_350g, 2)
    elif defects_per_350g <= 8:
        return "GRADE_2", round(defects_per_350g, 2)
    elif defects_per_350g <= 23:
        return "GRADE_3", round(defects_per_350g, 2)
    elif defects_per_350g <= 86:
        return "GRADE_4", round(defects_per_350g, 2)
    else:
        return "GRADE_5", round(defects_per_350g, 2)