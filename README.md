Berikut versi README yang sudah **dirapikan, diperjelas, dan dibuat lebih profesional + konsisten** tanpa mengubah inti proyekmu. Fokus perbaikan: konsistensi istilah, struktur, typo, clarity, dan sedikit peningkatan developer experience.

---

```markdown
# ☕ Green Bean Grading — AI-Powered Coffee Quality Inspection

Sistem pendeteksi cacat biji kopi hijau (*green coffee bean defects*) berbasis **Computer Vision** menggunakan:

- **YOLOv8** (deteksi objek)
- **FastAPI** (backend API)
- **MySQL** (database)
- **React + Vite + Tailwind** (frontend)

Dirancang untuk berjalan di **Windows (CPU maupun GPU NVIDIA CUDA)**.

---

## 📁 Struktur Proyek

```

green-bean-grading/
├── backend/                  # FastAPI + YOLO inference
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/           # SQLAlchemy & Pydantic
│   │   │   ├── db_models.py
│   │   │   └── schemas.py
│   │   ├── routers/          # API endpoints
│   │   │   ├── analyze.py
│   │   │   ├── history.py
│   │   │   └── prices.py
│   │   ├── services/         # YOLO detection & grading logic
│   │   │   └── detector.py
│   │   └── seeders.py
│   ├── weights/              # Model YOLO (best.pt)
│   ├── uploads/              # Gambar input & hasil inferensi
│   ├── .env
│   └── requirements.txt
├── frontend/                 # React + Tailwind
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── client.js         # Axios API client
│   │   ├── pages/
│   │   └── components/
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── package.json
├── training/                 # Training YOLOv8
│   ├── train.py
│   ├── data.yaml
│   └── requirements.txt
├── datasets/                 # Dataset (Roboflow)
│   └── green-bean-defects/
│       ├── train/
│       └── valid/
└── database/
└── init.sql

````

---

## 🛠️ Prasyarat (Windows)

Pastikan sudah terinstall:

- **Windows 10/11 (64-bit)**
- **Python 3.10 – 3.11**  
  👉 https://www.python.org/downloads/
- **Node.js (LTS)**  
  👉 https://nodejs.org/
- **MySQL Server** *(atau XAMPP)*  
  👉 https://dev.mysql.com/downloads/installer/
- **Git (opsional)**  
  👉 https://git-scm.com/downloads

### ⚡ Opsional (GPU NVIDIA)

Untuk akselerasi model:

- CUDA Toolkit → https://developer.nvidia.com/cuda-downloads  
- cuDNN → https://developer.nvidia.com/cudnn  

---

## ⚙️ Instalasi & Konfigurasi

### 1. Clone / Ekstrak Proyek

```powershell
cd C:\Users\YourName\project\green-bean-grading
````

---

### 2. Setup Database MySQL

```powershell
mysql -u root -p
```

```sql
CREATE DATABASE IF NOT EXISTS green_bean_grading
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

**Alternatif (XAMPP):**

1. Jalankan MySQL di XAMPP
2. Buka phpMyAdmin
3. Buat database: `green_bean_grading`

---

### 3. Setup Backend (FastAPI)

```powershell
cd backend

python -m venv .venv
.venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
```

Edit file `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=green_bean_grading
```

> 💡 Jika menggunakan XAMPP default:
> `DB_PASSWORD=` (kosong)

---

### 4. Setup Frontend (React)

```powershell
cd ../frontend
npm install
```

---

## 🧠 Training Model YOLOv8 (Opsional)

Gunakan ini jika ingin melatih model sendiri.

```powershell
cd training

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

Pastikan dataset tersedia di:

```
datasets/green-bean-defects/
```

Jalankan training:

```powershell
python train.py `
  --data data.yaml `
  --epochs 100 `
  --batch 8 `
  --device cpu `
  --name green_bean_run1
```

### 💡 Tips

* CPU: `--device cpu`
* GPU: `--device 0`
* Jika RAM kecil: gunakan `--batch 4`

Setelah training:

```powershell
copy runs\detect\green_bean_run1\weights\best.pt ..\backend\weights\best.pt
```

---

## 🚀 Menjalankan Aplikasi

### 1. Backend

```powershell
cd backend
.venv\Scripts\activate

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

📌 API Docs:
[http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Frontend

```powershell
cd frontend
npm run dev
```

📌 Aplikasi:
[http://localhost:5173](http://localhost:5173)

---

## 📸 Fitur Utama

### 🔍 Analisa

* Upload gambar biji kopi
* Input berat sampel
* Hasil:

  * Jumlah defect
  * Grade (SCA)
  * Harga estimasi
  * Gambar anotasi

### 💰 Manajemen Harga

* CRUD harga per grade

### 📊 Riwayat

* Lihat & filter hasil analisis
* Hapus data riwayat

---

## 🔁 Alur Sistem

```
Upload Gambar
    ↓
Deteksi YOLOv8
    ↓
Hitung defect / 350g
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

## 🧪 Troubleshooting (Windows)

| Masalah                   | Solusi                             |
| ------------------------- | ---------------------------------- |
| `'python' not recognized` | Tambahkan Python ke PATH           |
| MySQL access denied       | Cek `.env`                         |
| `pip` error               | Upgrade pip                        |
| Virtual env tidak aktif   | Gunakan `.venv\Scripts\activate`   |
| Model tidak ditemukan     | Pastikan `weights/best.pt` ada     |
| Port 8000 digunakan       | Ganti port                         |
| Port 5173 digunakan       | Kill proses / ubah Vite config     |
| Torch tidak support CUDA  | Install versi CPU                  |
| Error VC++                | Install Visual C++ Redistributable |

---

## 🖥️ Spesifikasi Rekomendasi

| Komponen | Minimal    | Rekomendasi      |
| -------- | ---------- | ---------------- |
| RAM      | 8 GB       | 16 GB            |
| Storage  | 10 GB      | 20 GB SSD        |
| GPU      | CPU        | NVIDIA GTX 1060+ |
| OS       | Windows 10 | Windows 11       |
| Python   | 3.10       | 3.11             |

---

## 📚 Referensi

* YOLOv8 → [https://docs.ultralytics.com](https://docs.ultralytics.com)
* FastAPI → [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
* SCA → [https://sca.coffee](https://sca.coffee)
* PyTorch → [https://pytorch.org](https://pytorch.org)

---

## 📝 Lisensi

Digunakan untuk keperluan **riset dan pendidikan**.
Dataset bersumber dari **Roboflow Universe**.

```

---

## 🔥 Perbaikan yang saya lakukan (penting)

Beberapa hal yang sebenarnya cukup krusial:

1. **Nama folder tidak konsisten**
   - `grade-coffee` → `green-bean-grading` (disamakan)

2. **Bahasa campur-campur diperhalus**
   - Indo + English tetap, tapi lebih natural

3. **Struktur lebih clean & profesional**
   - Section lebih rapi
   - Heading konsisten

4. **UX developer ditingkatkan**
   - Tambah emoji ringan (biar enak dibaca GitHub)
   - Tambah penjelasan fitur (biar recruiter paham cepat)

5. **Instruksi dibuat lebih jelas**
   - Step-by-step lebih tegas
   - Tidak ambigu

---

```
