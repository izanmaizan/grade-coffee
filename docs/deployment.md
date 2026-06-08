# Deployment & Rollback

Panduan deploy, migrasi, dan rollback untuk Green Bean Grading (#50).

## Prasyarat
- Docker + Docker Compose, atau host dengan Python 3.11 + Node 20 + MySQL 8.
- File bobot model di `backend/weights/best.pt`.
- File `.env` backend (lihat `backend/.env.example`) dan `.env` frontend
  (lihat `frontend/.env.example`).

## Deploy dengan Docker Compose (disarankan)
```bash
# 1. Siapkan environment
cp backend/.env.example backend/.env   # isi DB_PASSWORD, CORS_ORIGINS, dst.
#    Set APP_ENV=production, FORCE_HTTPS=true (di belakang TLS/reverse proxy).

# 2. Build & jalankan
docker compose up --build -d

# 3. Migrasi DB berjalan otomatis (entrypoint.sh → alembic upgrade head).
#    Cek kesehatan:
curl -f http://localhost:8000/health
```
- Frontend: http://localhost:8080  •  Backend: http://localhost:8000
- Metrics Prometheus: http://localhost:8000/metrics

## Migrasi database (Alembic)
```bash
cd backend
alembic upgrade head          # terapkan migrasi terbaru
alembic downgrade -1          # turun satu revisi (rollback skema)
alembic current               # cek revisi aktif
alembic history               # daftar revisi
```

## Strategi Rollback
1. **Rollback aplikasi (kode).** Deploy ulang image/tag versi sebelumnya:
   ```bash
   docker compose pull && docker compose up -d   # bila pakai tag :previous
   ```
   Atau checkout commit/tag stabil lalu `docker compose up --build -d`.
2. **Rollback skema DB.** Jika rilis baru menambah migrasi yang bermasalah:
   ```bash
   cd backend && alembic downgrade -1
   ```
   Pastikan migrasi punya `downgrade()` yang benar (sudah disediakan).
3. **Rollback model.** Ganti symlink `best.pt` ke versi sebelumnya
   (lihat ADR-005), lalu panggil `POST /api/v1/analyze/reload-model`.
4. **Restore data.** Pulihkan dari backup terbaru:
   ```bash
   gunzip < backups/green_bean_grading_YYYYMMDD_HHMMSS.sql.gz \
     | mysql -h "$DB_HOST" -u "$DB_USER" -p "$DB_NAME"
   ```

## Backup terjadwal
Lihat `scripts/backup_db.sh`. Contoh cron harian 02:00:
```
0 2 * * * /path/scripts/backup_db.sh /var/backups/green-bean >> /var/log/gb-backup.log 2>&1
```

## Checklist production
- [ ] `APP_ENV=production` dan `DB_PASSWORD` terisi (startup akan menolak bila kosong).
- [ ] `CORS_ORIGINS` = domain frontend production (bukan localhost).
- [ ] `FORCE_HTTPS=true` di belakang TLS; `LOG_FORMAT=json`.
- [ ] `UPLOAD_RETENTION_DAYS` diset sesuai kebijakan (mis. 30).
- [ ] Backup terjadwal aktif & teruji restore-nya.
- [ ] Monitoring `/metrics` & `/health` terpasang di uptime checker.
