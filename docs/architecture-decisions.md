# Architecture Decision Records (ADR)

Dokumen ini mencatat keputusan arsitektur penting beserta alasannya (#53),
agar developer baru (atau Anda sendiri di masa depan) tahu mana yang punya
alasan khusus dan mana yang bebas diubah.

---

## ADR-001: Deteksi memakai YOLOv8 (Ultralytics)

**Keputusan.** Deteksi defect memakai YOLOv8 lewat paket `ultralytics`.

**Alasan.** Object detection diperlukan karena satu gambar berisi banyak biji;
kita butuh lokasi + kelas tiap defect, bukan sekadar klasifikasi seluruh gambar.
YOLOv8 cepat di edge device (MacBook M-series via MPS) dan punya tooling training
yang matang.

**Konsekuensi.** Bobot model (`weights/best.pt`) adalah artefak terpisah, tidak
ikut di-commit (lihat `.gitignore`). Lihat ADR-005 soal versioning model.

---

## ADR-002: Detector sebagai singleton

**Keputusan.** `BeanDetector` memakai pola singleton.

**Alasan.** Loading model YOLO ke memori mahal (detik-an). Singleton memastikan
model di-load sekali per proses dan dipakai ulang antar-request.

**Konsekuensi.** Inference bersifat blocking dan berbagi satu instance. Untuk
mencegah event loop ter-blok, inference dipindah ke thread pool via
`asyncio.to_thread` di router (lihat ADR-004). Untuk skala lebih besar,
pertimbangkan worker proses terpisah / antrian (Celery, RQ) atau menaikkan
jumlah uvicorn workers.

---

## ADR-003: MySQL + SQLAlchemy (sinkron) + Alembic

**Keputusan.** Database MySQL diakses lewat SQLAlchemy sinkron (driver PyMySQL).
Skema dikelola migrasi Alembic, bukan `create_all()`.

**Alasan.** Query di aplikasi ini ringan dan jarang; bottleneck ada di inference,
bukan DB. Migrasi Alembic memungkinkan perubahan skema terkontrol & rollback,
syarat untuk deployment yang aman.

**Konsekuensi.** Kita sengaja TIDAK migrasi ke async DB (asyncmy/aiomysql).
Migrasi penuh berisiko tinggi (menyentuh semua router) dengan manfaat kecil untuk
beban kerja ini. Sebagai gantinya, operasi berat dipindah ke thread (ADR-004) dan
connection pool dikonfigurasi eksplisit di `app/database.py`.

---

## ADR-004: Operasi berat di thread pool, bukan async DB

**Keputusan.** File I/O upload, pemrosesan gambar (Pillow), dan inference YOLO
dijalankan via `asyncio.to_thread`, dengan timeout pada inference.

**Alasan.** Ini memberi konkurensi nyata tanpa biaya/risiko migrasi async DB.
Event loop tetap responsif saat inference berjalan.

---

## ADR-005: Versioning model sederhana berbasis file

**Keputusan.** Versi model diidentifikasi dari nama file + mtime
(`best.pt@<mtime>`). Untuk versioning eksplisit, simpan `best_vX.Y.Z.pt` dan
symlink `best.pt` ke versi aktif.

**Alasan.** Cukup untuk audit/log "model mana yang dipakai" tanpa menambah
infrastruktur. Bila kebutuhan meningkat, naikkan ke registry (MLflow/DVC).

---

## ADR-006: Tanpa autentikasi (by design)

**Keputusan.** API tidak memakai autentikasi.

**Alasan.** Layanan ditujukan untuk akses umum/internal terbuka sesuai kebutuhan
produk saat ini. Sebagai gantinya, abuse ditekan dengan rate limiting per-IP
(`slowapi`), batas ukuran upload/body, validasi konten gambar, dan CORS yang
membatasi origin. Bila kelak butuh kontrol akses (mis. endpoint admin
`reload-model`), tambahkan API key/JWT di depan router admin.

---

## ADR-007: Penyimpanan gambar di filesystem lokal (dengan seam)

**Keputusan.** Gambar disimpan di filesystem lokal (`uploads/`), namun seluruh
akses dilewatkan lewat `app/services/storage.py`.

**Alasan.** Sederhana untuk skala saat ini. Abstraksi storage menjadi satu titik
ganti bila pindah ke object storage (S3/MinIO) — cukup ubah `save_*` dan
`build_url`. Retensi & monitoring disk sudah ditangani di modul yang sama.
