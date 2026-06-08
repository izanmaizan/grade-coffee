# ☕ Green Bean Grading — AI-Powered Coffee Quality Inspection

Sistem pendeteksi cacat biji kopi hijau (*green coffee bean defects*) berbasis **Computer Vision** menggunakan:

- **YOLOv8** — deteksi objek
- **FastAPI** — backend API
- **MySQL** — database
- **React + Vite + Tailwind** — frontend

---

## 📁 Struktur Proyek

```
grade-coffee/
├── backend/                  # FastAPI + YOLO inference
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/           # SQLAlchemy & Pydantic
│   │   ├── routers/          # API endpoints (analyze, history, prices)
│   │   └── services/         # YOLO detection & grading logic
│   ├── weights/              # Model YOLO (best.pt)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + Tailwind
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── training/                 # Training YOLOv8
│   ├── train.py
│   └── data.yaml
├── datasets/
│   └── coffee-bean/          # Dataset gabungan (9 kelas)
├── docker-compose.yml
└── .env
```

---

## 🚀 Menjalankan Aplikasi (Windows — Docker Desktop)

Cara termudah menjalankan proyek ini di Windows adalah menggunakan **Docker Desktop**. Tidak perlu install Python, Node.js, atau MySQL secara manual.

### Prasyarat

- **Windows 10/11 (64-bit)**
- **Docker Desktop untuk Windows**
  👉 https://www.docker.com/products/docker-desktop/
  > Saat instalasi, aktifkan opsi **"Use WSL 2"** (direkomendasikan)

---

### Langkah 1 — Clone / Ekstrak Proyek

```powershell
git clone <url-repo>
cd grade-coffee
```

Atau ekstrak ZIP ke folder pilihan, lalu buka **PowerShell** / **Terminal** di dalam folder tersebut.

---

### Langkah 2 — Buat File `.env`

Buat file `.env` di root folder proyek (sejajar dengan `docker-compose.yml`):

```env
APP_ENV=development

DB_NAME=green_bean_grading
DB_USER=root
DB_PASSWORD=

CORS_ORIGINS=http://localhost:8080
```

> File ini sudah ada di repo, cukup pastikan isinya sesuai di atas.

---

### Langkah 3 — Pastikan Model Ada

Pastikan file model `backend/weights/best.pt` tersedia.  
Jika belum ada, minta file `best.pt` dari tim atau jalankan training terlebih dahulu (lihat bagian Training di bawah).

---

### Langkah 4 — Jalankan Docker

Buka **PowerShell** atau **Command Prompt** di folder proyek, lalu jalankan:

```powershell
docker compose up --build
```

Docker akan otomatis:
1. Mendownload image yang dibutuhkan (MySQL, Python, Node, Nginx)
2. Build image backend dan frontend
3. Menjalankan migrasi database
4. Menyalakan semua service

> Proses build pertama membutuhkan waktu ~5–15 menit tergantung koneksi internet.

---

### Langkah 5 — Akses Aplikasi

Setelah semua service berjalan (tidak ada error merah di terminal):

| Service | URL |
|---------|-----|
| **Aplikasi (Frontend)** | http://localhost:8080 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |

---

### Menghentikan Aplikasi

```powershell
docker compose down
```

Untuk menghentikan dan menghapus data database (reset total):

```powershell
docker compose down -v
```

---

### Menjalankan Ulang (setelah dihentikan)

Tidak perlu `--build` lagi kecuali ada perubahan kode:

```powershell
docker compose up
```

---

## 📸 Fitur Utama

### 🔍 Analisa Biji Kopi
- Upload gambar biji kopi hijau
- Input berat sampel
- Hasil: jumlah defect per kelas, grade (SCA), estimasi harga, gambar anotasi

### 💰 Manajemen Harga
- CRUD harga per grade

### 📊 Riwayat
- Lihat, filter, dan hapus hasil analisis sebelumnya

---

## 🔁 Alur Sistem

```
Upload Gambar
    ↓
Deteksi YOLOv8 (best.pt)
    ↓
Hitung defect per 350g
    ↓
Penentuan grade (SCA)
    ↓
Ambil harga dari database
    ↓
Simpan riwayat
    ↓
Tampilkan hasil
```

---

## 🧠 Training Model YOLOv8 (Opsional)

Gunakan ini jika ingin melatih ulang model dengan dataset sendiri.

### Prasyarat Training

- Python 3.10–3.12
- Virtual environment

```powershell
cd grade-coffee

python -m venv venv
venv\Scripts\activate

pip install -r training\requirements.txt
```

### Jalankan Training

```powershell
python training\train.py --data training\data.yaml --epochs 100
```

**Opsi tambahan:**

| Flag | Default | Keterangan |
|------|---------|------------|
| `--epochs` | 100 | Jumlah epoch |
| `--batch` | 16 | Batch size (kurangi jika RAM kecil, misal `--batch 8`) |
| `--device` | auto | `cpu` / `cuda` / `0` |
| `--model` | yolov8n.pt | Bisa pakai checkpoint `last.pt` untuk lanjut training |

### Salin Model ke Backend

Setelah training selesai:

```powershell
copy runs\detect\green_bean\weights\best.pt backend\weights\best.pt
```

Lalu rebuild container backend:

```powershell
docker compose up --build backend
```

---

## 🧪 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Docker Desktop tidak bisa dibuka | Pastikan WSL 2 aktif, restart PC |
| `port is already allocated` | Port 8080 atau 8000 dipakai aplikasi lain — tutup aplikasi tersebut |
| Backend restart terus | Cek isi `.env`, pastikan `APP_ENV=development` |
| `best.pt` tidak ditemukan | Pastikan file ada di `backend/weights/best.pt` |
| Build lambat | Wajar saat pertama kali, berikutnya lebih cepat karena cache |
| Database error | Jalankan `docker compose down -v` lalu `docker compose up --build` |

---

## 🖥️ Spesifikasi Rekomendasi

| Komponen | Minimal | Rekomendasi |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Storage | 10 GB | 20 GB SSD |
| OS | Windows 10 | Windows 11 |
| Docker Desktop | 4.x | Versi terbaru |

---

## 📚 Referensi

- YOLOv8 → https://docs.ultralytics.com
- FastAPI → https://fastapi.tiangolo.com
- Docker Desktop → https://docs.docker.com/desktop/
- SCA Grading → https://sca.coffee

---

## 📝 Lisensi

Digunakan untuk keperluan **riset dan pendidikan**.  
Dataset bersumber dari **Roboflow Universe** (CC BY 4.0).
