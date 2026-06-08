#!/usr/bin/env bash
# ============================================
# Backup database MySQL Green Bean Grading (#45)
# ============================================
# Pemakaian:
#   ./scripts/backup_db.sh [folder_tujuan]
#
# Variabel lingkungan (atau dari backend/.env):
#   DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
#   BACKUP_RETENTION_DAYS   (default 14)
#   BACKUP_S3_BUCKET        (opsional, mis. s3://my-bucket/backups)
#
# Disarankan dijadwalkan via cron, contoh harian 02:00:
#   0 2 * * * /path/scripts/backup_db.sh /var/backups/green-bean >> /var/log/gb-backup.log 2>&1
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../backend/.env"

# Muat .env bila ada (tanpa menimpa env yang sudah diset)
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source <(grep -E '^(DB_|BACKUP_)' "$ENV_FILE" | sed 's/\r$//')
  set +a
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_NAME="${DB_NAME:-green_bean_grading}"
RETENTION="${BACKUP_RETENTION_DAYS:-14}"
DEST_DIR="${1:-${SCRIPT_DIR}/../backups}"

mkdir -p "$DEST_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="${DEST_DIR}/${DB_NAME}_${TS}.sql.gz"

echo "[backup] Dump ${DB_NAME} → ${OUT}"
MYSQL_PWD="${DB_PASSWORD:-}" mysqldump \
  --host="$DB_HOST" --port="$DB_PORT" --user="$DB_USER" \
  --single-transaction --quick --routines --triggers \
  "$DB_NAME" | gzip > "$OUT"

echo "[backup] Selesai ($(du -h "$OUT" | cut -f1))"

# Upload ke S3 bila dikonfigurasi
if [[ -n "${BACKUP_S3_BUCKET:-}" ]]; then
  echo "[backup] Upload ke ${BACKUP_S3_BUCKET}"
  aws s3 cp "$OUT" "${BACKUP_S3_BUCKET}/"
fi

# Hapus backup lokal lebih tua dari retensi
echo "[backup] Membersihkan backup > ${RETENTION} hari"
find "$DEST_DIR" -name "${DB_NAME}_*.sql.gz" -type f -mtime "+${RETENTION}" -delete

echo "[backup] OK"
