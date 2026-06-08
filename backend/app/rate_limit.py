"""
Rate limiter bersama (#3).

Memakai slowapi (berbasis limits). Key berdasarkan alamat IP remote — wajar
untuk layanan publik tanpa autentikasi: membatasi penyalahgunaan per-klien
sambil tetap melayani semua pengguna secara adil.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)
