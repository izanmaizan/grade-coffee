```markdown
# Panduan Instalasi Green Bean Grading - Windows

## 📋 Daftar File yang Perlu Disesuaikan untuk Windows

### File yang HARUS diubah:

| No | File Path | Perubahan | Prioritas |
|----|-----------|-----------|-----------|
| 1 | `backend/.env` | Konfigurasi database (password MySQL) | 🔴 Wajib |
| 2 | `backend/app/config.py` | Path separator untuk Windows | 🟡 Perlu dicek |
| 3 | `backend/app/services/detector.py` | Device detection untuk Windows | 🟡 Perlu dicek |
| 4 | `training/train.py` | Path separator dan device | 🟡 Perlu dicek |
| 5 | `training/data.yaml` | Path dataset absolut | 🟡 Perlu dicek |

### File yang TIDAK perlu diubah (kompatibel cross-platform):
- `backend/app/routers/*.py` - semua router
- `backend/app/models/*.py` - models dan schemas
- `backend/app/database.py` - menggunakan path dari config
- `frontend/**/*` - frontend tidak terpengaruh OS
- `backend/requirements.txt` - dependencies sama

---

## 🚀 Panduan Instalasi Lengkap Windows

### Langkah 1: Persiapan Environment Windows

#### 1.1 Install Python 3.11
```powershell
# Download dari https://www.python.org/downloads/
# PASTIAN centang "Add Python to PATH" saat instalasi

# Verifikasi instalasi
python --version
# Output: Python 3.11.x
```

#### 1.2 Install Node.js
```powershell
# Download dari https://nodejs.org/ (pilih LTS)

# Verifikasi
node --version
npm --version
```

#### 1.3 Install MySQL (pilih salah satu)

**Opsi A: MySQL Installer (Recommended)**
```powershell
# Download dari https://dev.mysql.com/downloads/installer/
# Pilih "Developer Default"
# Set password root (catat baik-baik!)
# Port default: 3306
```

**Opsi B: XAMPP (Lebih mudah untuk pemula)**
```powershell
# Download dari https://www.apachefriends.org/
# Install, lalu jalankan MySQL dari XAMPP Control Panel
# Default: no password for root
```

### Langkah 2: Setup Project Structure

```powershell
# Buka PowerShell sebagai Administrator
cd C:\
mkdir project
cd project
mkdir grade-coffee
cd grade-coffee

# Extract file proyek ke folder ini
# Atau clone dari repository
```

### Langkah 3: Setup Database

#### 3.1 Buka MySQL Command Line

**Jika pakai MySQL Installer:**
```powershell
mysql -u root -p
# Masukkan password root yang sudah dibuat
```

**Jika pakai XAMPP:**
```powershell
# Buka XAMPP Control Panel
# Start MySQL service
# Buka cmd, lalu:
cd C:\xampp\mysql\bin
mysql -u root
```

#### 3.2 Create Database
```sql
CREATE DATABASE IF NOT EXISTS green_bean_grading
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

SHOW DATABASES;
-- Pastikan green_bean_grading muncul

EXIT;
```

### Langkah 4: Konfigurasi Backend

#### 4.1 Setup Virtual Environment
```powershell
cd C:\project\grade-coffee\backend

# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment
.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### 4.2 Install Dependencies
```powershell
# Install semua package
pip install -r requirements.txt

# Jika ada error dengan torch (CUDA), install versi CPU:
pip uninstall torch torchvision -y
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu
```

#### 4.3 Buat File .env

Salin dari template `.env.example` (JANGAN commit file `.env` — sudah masuk
`.gitignore`):
```powershell
# Di folder backend
Copy-Item .env.example .env
```
```bash
# macOS / Linux
cp .env.example .env
```

Lalu edit `.env` dan **ganti placeholder** sesuai lingkungan Anda. Yang wajib
diperhatikan:

```env
APP_ENV=development                 # 'production' saat deploy
DB_USER=green_bean_user
DB_PASSWORD=GANTI_DENGAN_PASSWORD    # WAJIB diisi di production
DB_NAME=green_bean_grading
MODEL_PATH=weights/best.pt           # Windows boleh pakai weights\best.pt
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CONFIDENCE_THRESHOLD=0.05            # nilai hasil tuning model saat ini
IOU_THRESHOLD=0.3
DEVICE=auto                          # 'auto' | 'cpu' | 'mps' | 'cuda'
```

> Semua opsi lain (connection pool, rate limit, kompresi gambar, retensi upload,
> logging) sudah ada di `.env.example` lengkap dengan komentar. Variabel yang
> tidak dikenal akan **ditolak saat startup** (mencegah typo diam-diam), jadi
> jangan menambah key sembarangan.

#### 4.4 Siapkan Folder dan Model
```powershell
# Buat folder weights jika belum ada
New-Item -ItemType Directory -Force -Path weights

# Buat folder uploads jika belum ada  
New-Item -ItemType Directory -Force -Path uploads

# Copy file model best.pt ke folder weights
# Jika belum punya model, system akan warning tapi tetap jalan
```

### Langkah 5: Konfigurasi Training (Opsional)

#### 5.1 Edit data.yaml
Buka `training/data.yaml` dengan text editor:
```yaml
# Windows path format
path: C:/project/grade-coffee/datasets/green-bean-defects
train: train/images
val: valid/images

nc: 16
names:
  0: broken
  1: cut
  2: dry_cherry
  3: fade
  4: floater
  5: full_black
  6: full_sour
  7: fungus
  8: husk
  9: immature
  10: parchment
  11: partial_black
  12: partial_sour
  13: severe_insect_damage
  14: shell
  15: withered
```

#### 5.2 Setup Training Environment
```powershell
cd C:\project\grade-coffee\training

# Buat virtual environment terpisah
python -m venv .venv_train
.venv_train\Scripts\activate

pip install -r requirements.txt
```

### Langkah 6: Setup Frontend

```powershell
cd C:\project\grade-coffee\frontend

# Install dependencies
npm install

# Jika error, coba:
npm cache clean --force
npm install
```

---

## 🔧 Modifikasi Source Code (Jika Perlu)

### File 1: `backend/app/config.py`
```python
# Cek bagian BASE_DIR - seharusnya sudah otomatis kompatibel
# Tapi jika ada masalah, ubah jadi:
BASE_DIR = Path(__file__).resolve().parent.parent

# Untuk Windows, pastikan path join pakai Path object
# JANGAN pakai string concatenation dengan + atau /
```

### File 2: `backend/app/services/detector.py`
```python
# Di bagian _resolve_device, Windows tidak support MPS:
def _resolve_device(requested: str) -> str:
    if requested == "auto":
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    return requested

# Hapus atau comment bagian MPS:
# if torch.backends.mps.is_available():
#     return "mps"
```

### File 3: `training/train.py`
```python
# Di fungsi pilih_device, comment bagian MPS:
def pilih_device(requested: str) -> str:
    import torch
    if requested != "auto":
        return requested
    # if torch.backends.mps.is_available():  # Comment untuk Windows
    #     return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"
```

---

## 🚀 Menjalankan Aplikasi

### Terminal 1: Backend Server
```powershell
# Buka PowerShell baru
cd C:\project\grade-coffee\backend
.venv\Scripts\activate

# Jalankan server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Output yang diharapkan:
# ✅ Green Bean Grading API siap di http://localhost:8000
# 📖 Dokumentasi: http://localhost:8000/docs
```

### Terminal 2: Frontend
```powershell
# Buka PowerShell baru
cd C:\project\grade-coffee\frontend

# Jalankan dev server
npm run dev

# Output:
# VITE v5.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

### Buka Aplikasi
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🧪 Testing Instalasi

### Test Backend API
```powershell
# Buka PowerShell baru
curl http://localhost:8000/health

# Output yang diharapkan:
# {"status":"ok","model_ready":false,"device":"cpu"}
```

### Test Database Connection
```powershell
curl http://localhost:8000/api/prices

# Output: [] (array kosong karena belum ada data)
```

### Test Frontend
Buka browser: http://localhost:5173
- Halaman harus loading tanpa error
- Console browser (F12) tidak ada error merah

---

## ⚠️ Troubleshooting Windows

### Error 1: `Python not found`
```powershell
# Solusi: Gunakan 'py' instead of 'python'
py --version
py -m venv .venv
```

### Error 2: `pip install` gagal karena SSL
```powershell
# Solusi: Install dengan trust
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Error 3: `Can't open file 'uvicorn'`
```powershell
# Solusi: Gunakan python -m
python -m uvicorn app.main:app --reload
```

### Error 4: `Access denied for user 'root'`
```powershell
# Cek file .env, pastikan password benar
# Atau reset password MySQL:
# https://dev.mysql.com/doc/refman/8.0/en/resetting-permissions.html
```

### Error 5: Port 8000 already in use
```powershell
# Cek proses yang menggunakan port 8000
netstat -ano | findstr :8000

# Kill process (ganti PID dengan angka dari command di atas)
taskkill /PID 12345 /F

# Atau ganti port backend:
uvicorn app.main:app --reload --port 8001
```

### Error 6: `torch` not finding CUDA
```powershell
# Cek CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Jika False, install CPU version:
pip uninstall torch torchvision -y
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
```

### Error 7: Long path error di Windows
```powershell
# Enable long paths (run as Administrator)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f

# Atau pindah project ke root drive (C:\project)
```

### Error 8: `npm install` error
```powershell
# Clear cache dan retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Jika masih error, coba:
npm install --legacy-peer-deps
```

---

## ✅ Checklist Instalasi

Setelah selesai, pastikan semua ini terpenuhi:

- [ ] Python 3.10+ terinstall dan terdeteksi di PATH
- [ ] Node.js terinstall
- [ ] MySQL running (service berjalan)
- [ ] Database `green_bean_grading` sudah dibuat
- [ ] File `.env` sudah dikonfigurasi dengan benar
- [ ] Virtual environment backend aktif
- [ ] `pip install -r requirements.txt` berhasil
- [ ] Backend bisa running dengan `uvicorn`
- [ ] `npm install` di frontend berhasil
- [ ] Frontend bisa running dengan `npm run dev`
- [ ] Bisa akses http://localhost:5173
- [ ] Bisa akses http://localhost:8000/docs
- [ ] Model `best.pt` sudah ada di folder `backend/weights/`

---

## 📞 Dukungan

Jika masih ada masalah:

1. Cek log error di terminal (backend dan frontend)
2. Cek console browser (F12)
3. Pastikan semua port tidak bertabrakan
4. Verifikasi PATH environment variables

---

## 🔄 Update dari Mac ke Windows

Perbedaan utama yang sudah diakomodasi:

| Aspek | Mac | Windows |
|-------|-----|---------|
| Path separator | `/` | `\` atau `/` |
| Virtual env activation | `source .venv/bin/activate` | `.venv\Scripts\activate` |
| Copy command | `cp` | `copy` |
| Python command | `python3` | `python` |
| GPU acceleration | MPS | CUDA / CPU |
| Line continuation | `\` | `` ` `` (PowerShell) |

---

**Selamat! Aplikasi Green Bean Grading siap digunakan di Windows.** 🎉
```

Panduan ini sudah mencakup:
1. ✅ Daftar file yang perlu diubah
2. ✅ Langkah instalasi detail untuk Windows
3. ✅ Modifikasi kode yang diperlukan
4. ✅ Troubleshooting spesifik Windows
5. ✅ Checklist verifikasi instalasi