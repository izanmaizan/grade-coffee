"""
Konfigurasi aplikasi Green Bean Grading.
Memuat variabel lingkungan dari file .env.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


# Direktori root backend (1 level di atas folder app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Konfigurasi yang dibaca dari .env file."""

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "green_bean_grading"

    # Model
    MODEL_PATH: str = "weights/best.pt"

    # Upload
    UPLOAD_DIR: str = "uploads"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Detection thresholds
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45

    # Device pilihan: 'auto', 'cpu', 'mps' (Mac M1/M2), 'cuda'
    DEVICE: str = "auto"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

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