"""
Konfigurasi logging terstruktur untuk seluruh aplikasi (#7).

- Mode 'console' (dev): output ringkas berwarna-netral dengan timestamp & level.
- Mode 'json' (production): satu baris JSON per log, siap di-ingest ELK/Datadog/
  CloudWatch.

Setiap log record otomatis menyertakan `request_id` bila tersedia (di-set oleh
middleware correlation-id) lewat ContextVar.
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

from app.config import settings


# Context var untuk menautkan log ke satu request (#24, #42)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Sisipkan request_id dari context ke setiap record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """Format log sebagai satu baris JSON."""

    # Atribut bawaan LogRecord yang tidak perlu diduplikasi ke "extra".
    _RESERVED = {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
        "request_id",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Sertakan field tambahan dari logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Format ringkas untuk development."""

    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", None)
        rid_part = f" [{rid[:8]}]" if rid else ""
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        base = f"{ts} {record.levelname:<7}{rid_part} {record.name}: {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging() -> None:
    """Pasang konfigurasi logging global. Dipanggil sekali saat startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL)

    # Selaraskan logger uvicorn agar tidak dobel format
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True

    logging.getLogger(__name__).info(
        "Logging siap", extra={"format": settings.LOG_FORMAT, "level": settings.LOG_LEVEL}
    )


def get_logger(name: str) -> logging.Logger:
    """Helper standar untuk mengambil logger bernama modul."""
    return logging.getLogger(name)
