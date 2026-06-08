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
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from app.config import settings
from app.logging_config import get_logger


logger = get_logger(__name__)


# Nama kelas (Inggris) — sesuai dataset coffee-bean-defect.v3i & green-coffee-bean-defect.v1i
# (keduanya identik, 9 kelas). Hanya fallback; sumber kebenaran = self.model.names.
CLASS_NAMES = [
    "black",      # 0  → primary
    "broken",     # 1  → secondary
    "foreign",    # 2  → primary (benda asing)
    "fraghusk",   # 3  → secondary (pecahan kulit)
    "green",      # 4  → GOOD (biji bagus, tidak dihitung)
    "husk",       # 5  → secondary
    "immature",   # 6  → secondary
    "infested",   # 7  → secondary (serangga)
    "sour",       # 8  → primary
]

# ==================================================
# TAKSONOMI DEFECT SCA — 9 kelas dataset (Green Arabica)
# ==================================================
# Bobot = "full defect equivalent" per biji (mengikuti rasio SCA):
#   PRIMARY (Category 1): 1 biji = 1 full defect  → bobot 1.0
#     (black, sour, foreign)
#   SECONDARY (Category 2): 5 biji = 1 full defect → bobot 0.2
#     (broken, husk, fraghusk, immature); serangga 10:1 → 0.1 (infested)
#   GOOD: biji bagus (green) TIDAK dihitung sebagai cacat.
# Sumber kebenaran tunggal untuk pembobotan — boleh dikalibrasi.
# Kategori ("primary"/"secondary"/"good") juga dipakai untuk pengelompokan UI.
PRIMARY = "primary"
SECONDARY = "secondary"
GOOD = "good"

# (kategori, full_defect_equivalent_per_biji)
DEFECT_TAXONOMY: dict[str, tuple[str, float]] = {
    # ---- 9 kelas kanonik dataset (coffee-bean-defect.v3i / green-coffee-bean-defect.v1i) ----
    "black":     (PRIMARY, 1.0),       # biji hitam
    "sour":      (PRIMARY, 1.0),       # biji asam
    "foreign":   (PRIMARY, 1.0),       # benda asing
    "broken":    (SECONDARY, 0.2),     # biji pecah
    "husk":      (SECONDARY, 0.2),     # kulit kopi
    "fraghusk":  (SECONDARY, 0.2),     # pecahan kulit
    "immature":  (SECONDARY, 0.2),     # biji muda
    "infested":  (SECONDARY, 0.1),     # rusak serangga (10:1)
    "green":     (GOOD, 0.0),          # biji bagus (tidak dihitung)
    # ---- Alias aman (jaga-jaga bila penamaan model sedikit berbeda) ----
    "full_black": (PRIMARY, 1.0),
    "full_sour":  (PRIMARY, 1.0),
    "foreign_matter": (PRIMARY, 1.0),
    "normal":    (GOOD, 0.0),
    "good":      (GOOD, 0.0),
    # ---- Kompat transisi: nama Indonesia (model best.pt LAMA, sebelum retrain) ----
    "hitam_penuh":           (PRIMARY, 1.0),
    "asam_penuh":            (PRIMARY, 1.0),
    "kopi_gelondong":        (PRIMARY, 1.0),
    "jamur":                 (PRIMARY, 1.0),
    "rusak_serangga_parah":  (PRIMARY, 0.2),
    "hitam_sebagian":        (SECONDARY, 0.3333),
    "asam_sebagian":         (SECONDARY, 0.3333),
    "pecah":                 (SECONDARY, 0.2),
    "terpotong":             (SECONDARY, 0.2),
    "kulit_kopi":            (SECONDARY, 0.2),
    "kulit_tanduk":          (SECONDARY, 0.2),
    "mentah":                (SECONDARY, 0.2),
    "pudar":                 (SECONDARY, 0.2),
    "mengapung":             (SECONDARY, 0.2),
    "cangkang":              (SECONDARY, 0.2),
    "layu":                  (SECONDARY, 0.2),
}
# Default untuk kelas tak dikenal: anggap cacat secondary ringan.
DEFAULT_TAXONOMY = (SECONDARY, 0.2)


def _resolve_device(requested: str) -> str:
    """Pilih device terbaik berdasarkan ketersediaan hardware."""
    if requested == "auto":
        if torch.backends.mps.is_available():
            return "mps"  # MacBook M1/M2/M3
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return requested


class ModelNotReadyError(RuntimeError):
    """Dilempar saat inference dipanggil tapi model belum tersedia."""


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
        self.model_version = self._read_model_version()

        # Load model jika file ada
        if self.model_path.exists():
            self._load_model()
        else:
            msg = f"Model tidak ditemukan di {self.model_path}"
            if settings.require_model:
                # Production / REQUIRE_MODEL_ON_STARTUP=true → gagal keras (#13)
                logger.error(msg)
                raise FileNotFoundError(
                    f"{msg}. Aplikasi dikonfigurasi mewajibkan model saat startup "
                    "(APP_ENV=production atau REQUIRE_MODEL_ON_STARTUP=true)."
                )
            logger.warning(
                "%s — endpoint /api/analyze akan mengembalikan 503 sampai model tersedia",
                msg,
            )

        self._initialized = True

    def _read_model_version(self) -> str:
        """
        Tentukan versi model untuk audit/log (#44).

        Memakai nama file + mtime sebagai penanda versi sederhana. Untuk
        versioning eksplisit, simpan model sebagai best_vX.Y.Z.pt dan symlink
        best.pt ke versi aktif.
        """
        try:
            if self.model_path.exists():
                stat = self.model_path.stat()
                return f"{self.model_path.name}@{int(stat.st_mtime)}"
        except OSError as exc:
            logger.warning("Gagal membaca versi model", extra={"error": str(exc)})
        return "unknown"

    def _load_model(self):
        """Load YOLO model ke memory."""
        logger.info(
            "Loading YOLO model",
            extra={"path": str(self.model_path), "device": self.device,
                   "version": self.model_version},
        )
        self.model = YOLO(str(self.model_path))

        # Warm up model (forward pass kosong) supaya request pertama tidak lambat
        try:
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(dummy, device=self.device, verbose=False, imgsz=640)
            logger.info("Model siap digunakan (warm-up sukses)")
        except (RuntimeError, ValueError) as exc:
            # Warm-up gagal tidak fatal, tapi tetap dicatat lengkap (#48)
            logger.warning("Warm-up model gagal (tidak fatal)", exc_info=exc)

    def is_ready(self) -> bool:
        return self.model is not None

    def reload(self):
        """Reload model — dipakai kalau weights di-update tanpa restart."""
        if self.model_path.exists():
            self.model_version = self._read_model_version()
            self._load_model()
        else:
            logger.warning(
                "Reload diminta tapi model tidak ditemukan",
                extra={"path": str(self.model_path)},
            )

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
            raise ModelNotReadyError(
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

        logger.info(
            "Deteksi selesai",
            extra={
                "total_defects": len(detections),
                "elapsed_ms": elapsed_ms,
                "model_version": self.model_version,
            },
        )

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
# PERHITUNGAN NILAI CACAT (SCA — full defect equivalent)
# ==================================================
class DefectValueResult(NamedTuple):
    """Hasil perhitungan nilai cacat untuk grading + transparansi bisnis."""
    defect_value_per_ref: float   # full defect equivalent dinormalisasi ke berat acuan
    raw_defect_value: float        # nilai cacat mentah (sesuai biji di foto)
    reference_gram: int            # berat acuan yang dipakai (mis. 300)
    berat_count: int               # jumlah biji cacat primary (Category 1)
    ringan_count: int              # jumlah biji cacat secondary (Category 2)
    good_count: int                # jumlah biji bagus (tidak dihitung sebagai cacat)


def classify_defect(class_name: str) -> str:
    """Kembalikan kategori ('primary'/'secondary'/'good') untuk satu kelas."""
    return DEFECT_TAXONOMY.get(class_name, DEFAULT_TAXONOMY)[0]


def calculate_defect_value(
    class_counts: Dict[str, int],
    weight_gram: float,
    reference_gram: int | None = None,
) -> DefectValueResult:
    """
    Hitung NILAI CACAT berbobot (SCA full defect equivalent) dari rincian per kelas.

    Tiap jenis defect punya bobot (lihat DEFECT_TAXONOMY). Cacat primary (hitam
    penuh, asam penuh, ceri kering, jamur) bernilai 1 full defect; cacat secondary
    (pecah, kulit, mentah, dll.) hanya pecahan. Biji bagus (green) TIDAK dihitung.
    Ini standar SCA Green Arabica yang menentukan mutu → harga jual.

    Nilai cacat dinormalisasi ke berat acuan (DEFECT_REFERENCE_GRAM), memakai berat
    sampel sebenarnya yang diinput pengguna (fleksibel, tidak wajib 300/350g).
    Penentuan GRADE di layer router berdasarkan ambang min/max di DB (data-driven).

    Memakai Decimal agar boundary tidak terpengaruh galat floating point (#12).

    Args:
        class_counts   : {nama_kelas: jumlah_deteksi}
        weight_gram    : berat sampel sebenarnya (gram), > 0
        reference_gram : berat acuan normalisasi (default settings.DEFECT_REFERENCE_GRAM)

    Returns:
        DefectValueResult

    Raises:
        ValueError: bila weight_gram <= 0.
    """
    if weight_gram <= 0:
        raise ValueError("weight_gram harus lebih besar dari 0")

    ref = reference_gram or settings.DEFECT_REFERENCE_GRAM

    raw_value = Decimal("0")
    primary_count = 0
    secondary_count = 0
    good_count = 0

    for class_name, count in class_counts.items():
        if count <= 0:
            continue
        category, value = DEFECT_TAXONOMY.get(class_name, DEFAULT_TAXONOMY)
        if category == GOOD:
            good_count += count
            continue  # biji bagus tidak menambah nilai cacat
        raw_value += Decimal(int(count)) * Decimal(str(value))
        if category == PRIMARY:
            primary_count += count
        else:
            secondary_count += count

    per_ref = (raw_value / Decimal(str(weight_gram)) * Decimal(ref)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return DefectValueResult(
        defect_value_per_ref=float(per_ref),
        raw_defect_value=float(raw_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        reference_gram=ref,
        berat_count=primary_count,
        ringan_count=secondary_count,
        good_count=good_count,
    )
