-- ============================================
-- Green Bean Grading — Database Initialization
-- ============================================
-- Jalankan sekali sebelum menjalankan backend:
--   mysql -u root -p < database/init.sql
--
-- Tabel akan otomatis dibuat oleh SQLAlchemy juga,
-- tapi script ini berguna untuk:
--   - Membuat database
--   - Membuat user khusus aplikasi (opsional)
-- ============================================

-- Buat database jika belum ada
CREATE DATABASE IF NOT EXISTS green_bean_grading
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE green_bean_grading;

-- (Opsional) Buat user khusus untuk aplikasi — lebih aman dari root
-- Hapus komentar di bawah jika ingin pakai:
-- CREATE USER IF NOT EXISTS 'gbg_user'@'localhost' IDENTIFIED BY 'gbg_password_2026';
-- GRANT ALL PRIVILEGES ON green_bean_grading.* TO 'gbg_user'@'localhost';
-- FLUSH PRIVILEGES;

-- Tampilkan info
SELECT
    'Database green_bean_grading siap digunakan!' AS status,
    NOW() AS created_at;