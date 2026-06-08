"""
Layanan penyimpanan & pemrosesan gambar.

Tanggung jawab:
  - Validasi konten gambar secara nyata (bukan sekadar ekstensi) memakai Pillow,
    sekaligus mencegah file polyglot/berbahaya (#4, #39).
  - Normalisasi & kompresi gambar agar lebih ringan sebelum disimpan (#4).
  - Monitoring kapasitas disk + pembersihan file lama sesuai retensi (#18).

Catatan scalability (#22): semua akses file dilewatkan melalui modul ini sebagai
satu "seam". Saat ingin pindah ke object storage (S3/MinIO), cukup ganti
implementasi fungsi save_* dan build_url di sini tanpa menyentuh router. Nama
file diberi prefix tanggal (YYYYMMDD) agar terkelompok kronologis tanpa perlu
subfolder, sehingga URL `/uploads/{nama}` tetap sederhana.
"""
import io
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple

from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.logging_config import get_logger


logger = get_logger(__name__)


# Format gambar yang diterima (hasil deteksi Pillow, bukan ekstensi user)
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "BMP", "WEBP", "MPO"}


class InvalidImageError(ValueError):
    """Konten upload bukan gambar valid / format tidak didukung."""


class DiskUsage(NamedTuple):
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float


def validate_and_save_upload(raw_bytes: bytes) -> Path:
    """
    Validasi konten gambar lalu simpan versi terkompresi ke folder upload.

    Args:
        raw_bytes: isi file mentah dari UploadFile.

    Returns:
        Path absolut file yang tersimpan.

    Raises:
        InvalidImageError: jika bytes bukan gambar valid atau format tak didukung.
    """
    # 1) Verifikasi integritas: Pillow akan menolak file rusak / non-gambar (#39)
    try:
        probe = Image.open(io.BytesIO(raw_bytes))
        probe.verify()  # cek struktur tanpa decode penuh
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("File bukan gambar yang valid") from exc

    fmt = (probe.format or "").upper()
    if fmt not in ALLOWED_PIL_FORMATS:
        raise InvalidImageError(
            f"Format gambar '{fmt or 'tidak dikenal'}' tidak didukung. "
            "Gunakan JPG, PNG, BMP, atau WEBP."
        )

    # 2) Buka ulang untuk diproses (verify() membuat objek tidak bisa dipakai lagi)
    image = Image.open(io.BytesIO(raw_bytes))

    # Normalisasi mode warna → RGB (buang alpha/CMYK yang menyulitkan JPEG)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    # 3) Resize bila melebihi dimensi maksimum (#4)
    if settings.IMAGE_COMPRESS_ENABLED:
        max_dim = settings.IMAGE_MAX_DIMENSION
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.LANCZOS)

    # 4) Simpan sebagai JPEG terkompresi dengan nama berprefix tanggal
    date_prefix = datetime.now().strftime("%Y%m%d")
    out_name = f"{date_prefix}_{uuid.uuid4().hex[:12]}.jpg"
    out_path = settings.upload_full_path / out_name

    save_kwargs = {}
    if settings.IMAGE_COMPRESS_ENABLED:
        save_kwargs = {"quality": settings.IMAGE_JPEG_QUALITY, "optimize": True}
    image.save(out_path, format="JPEG", **save_kwargs)

    logger.info(
        "Gambar disimpan",
        extra={
            "file": out_name,
            "src_format": fmt,
            "src_bytes": len(raw_bytes),
            "out_bytes": out_path.stat().st_size,
        },
    )
    return out_path


def build_url(file_path: str | None) -> str | None:
    """Bangun URL publik dari path file fisik. Seam untuk CDN/S3 (#22)."""
    if not file_path:
        return None
    return f"/uploads/{Path(file_path).name}"


def delete_files(*paths: str | None) -> None:
    """Hapus file fisik dengan aman; kegagalan dicatat, bukan ditelan (#15)."""
    for path_str in paths:
        if not path_str:
            continue
        try:
            Path(path_str).unlink(missing_ok=True)
        except OSError as exc:
            logger.error(
                "Gagal menghapus file", extra={"path": path_str, "error": str(exc)}
            )


def get_disk_usage() -> DiskUsage:
    """Statistik penggunaan disk pada partisi folder upload (#18)."""
    import shutil

    total, used, free = shutil.disk_usage(settings.upload_full_path)
    percent = round(used / total * 100, 1) if total else 0.0
    return DiskUsage(total, used, free, percent)


def check_disk_space() -> bool:
    """
    Cek apakah disk masih sehat. Memberi peringatan bila melewati ambang (#18).

    Returns:
        True bila masih di bawah ambang, False bila sudah melewati.
    """
    usage = get_disk_usage()
    if usage.percent_used >= settings.DISK_USAGE_WARN_PERCENT:
        logger.warning(
            "Penggunaan disk tinggi",
            extra={
                "percent_used": usage.percent_used,
                "free_mb": round(usage.free_bytes / 1024 / 1024, 1),
            },
        )
        return False
    return True


def cleanup_old_uploads() -> int:
    """
    Hapus file upload yang lebih tua dari UPLOAD_RETENTION_DAYS (#18).

    Returns:
        Jumlah file yang dihapus. 0 bila retensi dinonaktifkan.
    """
    days = settings.UPLOAD_RETENTION_DAYS
    if days <= 0:
        return 0

    cutoff = time.time() - days * 86400
    removed = 0
    for f in settings.upload_full_path.glob("*"):
        if not f.is_file():
            continue
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
                removed += 1
        except OSError as exc:
            logger.error(
                "Gagal menghapus file lama", extra={"path": str(f), "error": str(exc)}
            )

    if removed:
        logger.info("Pembersihan upload selesai", extra={"removed": removed, "retention_days": days})
    return removed
