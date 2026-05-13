import { useEffect, useState } from 'react'
import { pricesApi, formatRupiah } from '../client'
import { useToast } from '../App'
import Modal from '../components/Modal'
import { Plus, Edit, Trash2, DollarSign, Package, Loader2, Coffee } from 'lucide-react'

const emptyForm = {
  grade_code: '',
  grade_name: '',
  description: '',
  price_per_gram: 0,
  min_defects: 0,
  max_defects: null,
  color: '#6366f1',
}

export default function PricesPage() {
  const { addToast } = useToast()
  const [prices, setPrices] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ ...emptyForm })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  const fetchPrices = async () => {
    setLoading(true)
    try {
      const data = await pricesApi.list()
      setPrices(data)
    } catch {
      addToast('Gagal memuat data harga', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPrices() }, [])

  const openCreate = () => {
    setEditing(null)
    setForm({ ...emptyForm })
    setErrors({})
    setModalOpen(true)
  }

  const openEdit = (item) => {
    setEditing(item)
    setForm({
      grade_code: item.grade_code,
      grade_name: item.grade_name,
      description: item.description || '',
      price_per_gram: item.price_per_gram,
      min_defects: item.min_defects,
      max_defects: item.max_defects,
      color: item.color,
    })
    setErrors({})
    setModalOpen(true)
  }

  const validate = () => {
    const errs = {}
    if (!form.grade_code.trim()) errs.grade_code = 'Kode grade wajib diisi'
    if (!form.grade_name.trim()) errs.grade_name = 'Nama grade wajib diisi'
    if (form.price_per_gram < 0) errs.price_per_gram = 'Harga tidak boleh negatif'
    if (form.min_defects < 0) errs.min_defects = 'Min defect tidak boleh negatif'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSave = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      const payload = { ...form, max_defects: form.max_defects || null }
      if (editing) {
        await pricesApi.update(editing.id, payload)
        addToast('Grade berhasil diperbarui', 'success')
      } else {
        await pricesApi.create(payload)
        addToast('Grade baru berhasil ditambahkan', 'success')
      }
      setModalOpen(false)
      fetchPrices()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Gagal menyimpan'
      addToast(msg, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (item) => {
    if (!confirm(`Hapus grade "${item.grade_name}"?`)) return
    try {
      await pricesApi.remove(item.id)
      addToast('Grade dihapus', 'success')
      fetchPrices()
    } catch (err) {
      addToast(err.response?.data?.detail || 'Gagal menghapus', 'error')
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-display font-bold text-coffee-900">Manajemen Harga</h2>
          <p className="text-coffee-500 mt-1">Kelola grade & harga per gram green bean</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          <Plus size={16} /> Tambah Grade
        </button>
      </div>

      {/* Loading skeleton */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-4 w-24 bg-coffee-100 rounded mb-3" />
              <div className="h-3 w-full bg-coffee-50 rounded mb-2" />
              <div className="h-5 w-32 bg-coffee-100 rounded mt-4" />
            </div>
          ))}
        </div>
      ) : prices.length === 0 ? (
        <div className="card p-12 text-center">
          <Package size={40} className="mx-auto text-coffee-300 mb-3" />
          <p className="text-coffee-500 font-medium">Belum ada data grade</p>
          <p className="text-sm text-coffee-400 mb-4">Tambahkan grade pertama Anda</p>
          <button onClick={openCreate} className="btn-primary mx-auto">
            <Plus size={16} /> Tambah Grade
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {prices.map((item, idx) => {
            const gradeColor = item.color || '#808080'
            return (
              <div
                key={item.id}
                className="card p-6 relative overflow-hidden group transition-all duration-300 hover:-translate-y-1 animate-slide-up"
                style={{
                  animationDelay: `${idx * 80}ms`,
                  boxShadow: `0 12px 32px -8px ${gradeColor}22, 0 4px 12px -2px ${gradeColor}18`,
                }}
              >
                {/* Aksen dekoratif tanpa garis pinggir */}
                <div
                  className="absolute -top-10 -right-10 w-28 h-28 rounded-full opacity-[0.06] group-hover:opacity-[0.12] transition-opacity duration-500"
                  style={{ backgroundColor: gradeColor }}
                />
                <div
                  className="absolute -bottom-8 -left-8 w-24 h-24 rounded-full opacity-[0.04] group-hover:opacity-[0.08] transition-opacity duration-500"
                  style={{ backgroundColor: gradeColor }}
                />

                {/* Ikon kopi kecil */}
                <div className="absolute top-5 right-5 opacity-[0.06] group-hover:opacity-[0.14] transition-opacity duration-300">
                  <Coffee size={40} style={{ color: gradeColor }} />
                </div>

                <div className="relative">
                  {/* Badge grade */}
                  <div className="flex items-center gap-3 mb-4">
                    <span
                      className="badge font-bold text-white px-3 py-1 text-xs"
                      style={{ backgroundColor: gradeColor, boxShadow: `0 2px 8px ${gradeColor}40` }}
                    >
                      {item.grade_code}
                    </span>
                    <span className="text-xs text-coffee-400 font-mono">
                      {item.min_defects}{item.max_defects != null ? `–${item.max_defects}` : '+'} defect/350g
                    </span>
                  </div>

                  {/* Nama grade */}
                  <h3 className="text-lg font-semibold text-coffee-900 mb-2">{item.grade_name}</h3>

                  {/* Deskripsi */}
                  {item.description && (
                    <p className="text-sm text-coffee-500 mb-4 line-clamp-2">{item.description}</p>
                  )}

                  {/* Harga */}
                  <div className="flex items-end justify-between mt-4 pt-4 border-t border-coffee-100/60">
                    <div>
                      <p className="text-xs text-coffee-400 mb-0.5">Harga per gram</p>
                      <p className="text-xl font-bold text-coffee-900 font-display">
                        {formatRupiah(item.price_per_gram)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-coffee-400 mb-0.5">per 350g</p>
                      <p className="text-lg font-semibold text-coffee-700">
                        {formatRupiah(item.price_per_gram * 350)}
                      </p>
                    </div>
                  </div>

                  {/* Tombol aksi */}
                  <div className="absolute top-0 right-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 -translate-y-1">
                    <button onClick={() => openEdit(item)} className="btn-ghost text-coffee-600">
                      <Edit size={14} />
                    </button>
                    <button onClick={() => handleDelete(item)} className="btn-ghost text-red-500 hover:bg-red-50">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Modal Create/Edit (tidak diubah) */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? `Edit Grade: ${editing.grade_name}` : 'Tambah Grade Baru'}
        maxWidth="max-w-xl"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Kode Grade *</label>
              <input
                type="text"
                value={form.grade_code}
                onChange={(e) => setForm(f => ({ ...f, grade_code: e.target.value }))}
                placeholder="GRADE_1"
                className={`input ${errors.grade_code ? 'border-red-300 focus:ring-red-500/20' : ''}`}
                disabled={!!editing}
              />
              {errors.grade_code && <p className="text-xs text-red-500 mt-1">{errors.grade_code}</p>}
            </div>
            <div>
              <label className="label">Warna</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={form.color}
                  onChange={(e) => setForm(f => ({ ...f, color: e.target.value }))}
                  className="w-10 h-10 rounded-lg border border-coffee-200 cursor-pointer"
                />
                <input
                  type="text"
                  value={form.color}
                  onChange={(e) => setForm(f => ({ ...f, color: e.target.value }))}
                  className="input flex-1 font-mono text-sm"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="label">Nama Grade *</label>
            <input
              type="text"
              value={form.grade_name}
              onChange={(e) => setForm(f => ({ ...f, grade_name: e.target.value }))}
              placeholder="Specialty Grade"
              className={`input ${errors.grade_name ? 'border-red-300' : ''}`}
            />
            {errors.grade_name && <p className="text-xs text-red-500 mt-1">{errors.grade_name}</p>}
          </div>

          <div>
            <label className="label">Deskripsi</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
              rows={3}
              className="input"
              placeholder="Deskripsi kualitas grade..."
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">Harga/gram *</label>
              <input
                type="number"
                value={form.price_per_gram}
                onChange={(e) => setForm(f => ({ ...f, price_per_gram: Number(e.target.value) }))}
                className={`input ${errors.price_per_gram ? 'border-red-300' : ''}`}
              />
              {errors.price_per_gram && <p className="text-xs text-red-500 mt-1">{errors.price_per_gram}</p>}
            </div>
            <div>
              <label className="label">Min Defect</label>
              <input
                type="number"
                value={form.min_defects}
                onChange={(e) => setForm(f => ({ ...f, min_defects: Number(e.target.value) }))}
                className="input"
              />
            </div>
            <div>
              <label className="label">Max Defect</label>
              <input
                type="number"
                value={form.max_defects ?? ''}
                onChange={(e) => setForm(f => ({ ...f, max_defects: e.target.value ? Number(e.target.value) : null }))}
                className="input"
                placeholder="∞"
              />
            </div>
          </div>

          {/* Preview warna */}
          <div
            className="p-4 rounded-xl flex items-center gap-3"
            style={{
              backgroundColor: form.color + '15',
              boxShadow: `0 0 0 1px ${form.color}30`,
            }}
          >
            <DollarSign size={20} style={{ color: form.color }} />
            <div>
              <p className="text-sm font-semibold text-coffee-800">{form.grade_name || 'Nama Grade'}</p>
              <p className="text-xs text-coffee-500">
                {formatRupiah(form.price_per_gram)}/gram • {form.min_defects}{form.max_defects != null ? `–${form.max_defects}` : '+'} defect/350g
              </p>
            </div>
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button onClick={() => setModalOpen(false)} className="btn-secondary">Batal</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary">
              {saving ? <><Loader2 size={14} className="animate-spin" /> Menyimpan...</> : editing ? 'Simpan Perubahan' : 'Tambah Grade'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}