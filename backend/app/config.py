"""
Konfigurasi aplikasi Green Bean Grading.
Memuat variabel lingkungan dari file .env.

Semua key yang dipakai didefinisikan eksplisit di kelas Settings. Memakai
`extra="forbid"` supaya typo pada nama variabel langsung ketahuan saat startup
(bukan diabaikan diam-diam).
"""
from pathlib import Path
from typing import List, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Direktori root backend (1 level di atas folder app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Konfigurasi yang dibaca dari .env file."""

    # ----------------------------------------------------------------
    # Environment
    # ----------------------------------------------------------------
    # 'development' | 'production' — memengaruhi validasi & default aman.
    APP_ENV: Literal["development", "production"] = "development"

    # ----------------------------------------------------------------
    # Database
    # ----------------------------------------------------------------
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "green_bean_grading"

    # Connection pool (#10)
    DB_POOL_SIZE: int = Field(20, ge=1, le=200)
    DB_MAX_OVERFLOW: int = Field(40, ge=0, le=400)
    DB_POOL_TIMEOUT: int = Field(30, ge=1, le=300)
    DB_POOL_RECYCLE: int = Field(1800, ge=60, le=86400)
    # Retry koneksi DB saat startup (#49)
    DB_CONNECT_RETRIES: int = Field(5, ge=0, le=20)

    # ----------------------------------------------------------------
    # Model
    # ----------------------------------------------------------------
    MODEL_PATH: str = "weights/best.pt"
    # Jika True, startup gagal kalau model tidak ada (#13). Default mengikuti env.
    REQUIRE_MODEL_ON_STARTUP: bool | None = None
    # Timeout inference YOLO (detik) (#52)
    INFERENCE_TIMEOUT_SECONDS: float = Field(30.0, gt=0, le=300)

    # ----------------------------------------------------------------
    # Upload & storage
    # ----------------------------------------------------------------
    UPLOAD_DIR: str = "uploads"
    # Batas ukuran file upload dalam MB (#4)
    MAX_UPLOAD_MB: float = Field(10.0, gt=0, le=100)
    # Kompresi/normalisasi gambar agar lebih ringan (#4)
    IMAGE_COMPRESS_ENABLED: bool = True
    IMAGE_MAX_DIMENSION: int = Field(1920, ge=320, le=8000)
    IMAGE_JPEG_QUALITY: int = Field(85, ge=40, le=100)
    # Retensi file upload (hari). 0 = tidak pernah dihapus otomatis (#18)
    UPLOAD_RETENTION_DAYS: int = Field(0, ge=0, le=3650)
    # Ambang peringatan disk (persen terpakai) (#18)
    DISK_USAGE_WARN_PERCENT: int = Field(90, ge=50, le=100)

    # ----------------------------------------------------------------
    # CORS & security
    # ----------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    # Batas ukuran body request global (MB) (#40)
    MAX_REQUEST_BODY_MB: float = Field(15.0, gt=0, le=200)
    # Paksa redirect HTTP → HTTPS (#47). Aktifkan di prod di belakang TLS.
    FORCE_HTTPS: bool = False
    # Rate limit default untuk semua endpoint (#3)
    RATE_LIMIT_DEFAULT: str = "120/minute"
    # Rate limit khusus endpoint analyze yang berat (#3)
    RATE_LIMIT_ANALYZE: str = "10/minute"

    # ----------------------------------------------------------------
    # Detection thresholds
    # ----------------------------------------------------------------
    CONFIDENCE_THRESHOLD: float = Field(0.25, ge=0.01, le=0.99)
    IOU_THRESHOLD: float = Field(0.45, ge=0.01, le=0.99)

    # Grading
    # ----------------------------------------------------------------
    # Berat sampel acuan untuk normalisasi nilai cacat (SNI = 300g, SCA Arabika = 350g)
    DEFECT_REFERENCE_GRAM: int = Field(300, ge=50, le=1000)

    # Device pilihan: 'auto', 'cpu', 'mps' (Mac M1/M2), 'cuda'
    DEVICE: Literal["auto", "cpu", "mps", "cuda"] = "auto"

    # ----------------------------------------------------------------
    # Logging
    # ----------------------------------------------------------------
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # 'json' untuk production (mudah di-ingest), 'console' untuk dev.
    LOG_FORMAT: Literal["json", "console"] = "console"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",  # (#27) typo variabel langsung error, tidak diabaikan
    )

    # ----------------------------------------------------------------
    # Validators (#35)
    # ----------------------------------------------------------------
    @model_validator(mode="after")
    def _validate_production_safety(self) -> "Settings":
        """Pastikan konfigurasi aman saat APP_ENV=production."""
        if self.APP_ENV == "production":
            problems: list[str] = []
            if not self.DB_PASSWORD:
                problems.append("DB_PASSWORD wajib diisi di production")
            if any(
                o.startswith("http://localhost") or o.startswith("http://127.")
                for o in self.cors_origins_list
            ):
                problems.append(
                    "CORS_ORIGINS masih memakai localhost di production — "
                    "set ke domain produksi sebenarnya"
                )
            if problems:
                raise ValueError(
                    "Konfigurasi production tidak valid:\n  - "
                    + "\n  - ".join(problems)
                )
        return self

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _cors_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("CORS_ORIGINS tidak boleh kosong")
        return v

    # ----------------------------------------------------------------
    # Derived properties
    # ----------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def require_model(self) -> bool:
        """Apakah model wajib ada saat startup (#13)."""
        if self.REQUIRE_MODEL_ON_STARTUP is not None:
            return self.REQUIRE_MODEL_ON_STARTUP
        # Default: wajib di production, opsional di development.
        return self.is_production

    @property
    def max_upload_bytes(self) -> int:
        return int(self.MAX_UPLOAD_MB * 1024 * 1024)

    @property
    def max_request_body_bytes(self) -> int:
        return int(self.MAX_REQUEST_BODY_MB * 1024 * 1024)

    @property
    def database_url(self) -> str:
        """Bangun URL koneksi MySQL untuk SQLAlchemy."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse string CORS menjadi list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def model_full_path(self) -> Path:
        """Path absolut ke file model YOLO."""
        return BASE_DIR / self.MODEL_PATH

    @property
    def upload_full_path(self) -> Path:
        """Path absolut ke folder upload."""
        return BASE_DIR / self.UPLOAD_DIR


# Singleton settings
settings = Settings()

# Pastikan folder upload ada
settings.upload_full_path.mkdir(parents=True, exist_ok=True)
