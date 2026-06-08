/**
 * Konstanta bersama lintas-halaman (#20).
 * Sumber tunggal warna grade agar tidak duplikat di banyak file.
 */
export const GRADE_COLORS = {
  GRADE_1: '#10b981',
  GRADE_2: '#3b82f6',
  GRADE_3: '#f59e0b',
  GRADE_4: '#ef4444',
  GRADE_5: '#6b7280',
}

export const DEFAULT_GRADE_COLOR = '#808080'

/** Warna untuk badge per-kelas defect pada overlay. */
export const DEFECT_COLORS = [
  '#f87171', '#fb923c', '#fbbf24', '#a3e635', '#34d399', '#22d3ee',
  '#60a5fa', '#818cf8', '#c084fc', '#e879f9', '#fb7185', '#f97316',
  '#facc15', '#4ade80', '#2dd4bf', '#38bdf8',
]

/** Preset berat sampel (gram). 300g = acuan SCA. */
export const WEIGHT_PRESETS = [100, 250, 300, 500]

/** Validasi hex color #RGB atau #RRGGBB, selaras dengan backend (#14). */
export const HEX_COLOR_OK = (v) => /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v || '')
