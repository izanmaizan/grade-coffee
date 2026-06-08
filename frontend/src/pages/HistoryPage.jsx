import { useEffect, useState } from 'react'
import { historyApi, formatDate, formatRupiah, resolveAssetUrl } from '../client'
import { useToast } from '../App'
import { GRADE_COLORS, DEFAULT_GRADE_COLOR } from '../constants'
import { Search, Trash2, ChevronLeft, ChevronRight, History, ImageOff, Eye, Loader2, RefreshCw, X } from 'lucide-react'

export default function HistoryPage() {
  // useToast() mengembalikan fungsi addToast langsung, bukan object (#26)
  const addToast = useToast()
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filter, setFilter] = useState('')
  const [previewImg, setPreviewImg] = useState(null)
  const pageSize = 10

  const fetchData = async (p = page) => {
    setLoading(true)
    try {
      const data = await historyApi.list(p, pageSize, filter || null)
      setList(data.items || [])
      setTotal(data.total || 0)
    } catch (e) {
      addToast('Gagal memuat riwayat', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData(page) }, [page, filter])

  const handleDelete = async (id) => {
    if (!confirm('Hapus data ini?')) return
    try {
      await historyApi.remove(id)
      addToast('Data dihapus', 'success')
      fetchData(page)
    } catch {
      addToast('Gagal menghapus', 'error')
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-display font-bold text-coffee-900">Riwayat Analisa</h2>
          <p className="text-coffee-500 mt-1">{total} total analisa tersimpan</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-coffee-400" />
            <select
              value={filter}
              onChange={(e) => { setFilter(e.target.value); setPage(1) }}
              className="input pl-10 pr-4 py-2 text-sm w-40"
            >
              <option value="">Semua Grade</option>
              <option value="GRADE_1">Specialty</option>
              <option value="GRADE_2">Premium</option>
              <option value="GRADE_3">Commercial</option>
            </select>
          </div>
          <button onClick={() => fetchData(page)} className="btn-ghost text-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 size={24} className="animate-spin mx-auto text-bean-500 mb-3" />
            <p className="text-coffee-500">Memuat data...</p>
          </div>
        ) : list.length === 0 ? (
          <div className="p-12 text-center">
            <History size={40} className="mx-auto text-coffee-300 mb-3" />
            <p className="text-coffee-500 font-medium">Belum ada data analisa</p>
            <p className="text-sm text-coffee-400">Hasil analisa akan muncul di sini</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-coffee-50/70 border-b border-coffee-100">
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-coffee-500 uppercase tracking-wider">Tanggal</th>
                    <th className="px-5 py-3.5 text-left text-xs font-semibold text-coffee-500 uppercase tracking-wider">Berat</th>
                    <th className="px-5 py-3.5 text-center text-xs font-semibold text-coffee-500 uppercase tracking-wider">Defect</th>
                    <th className="px-5 py-3.5 text-center text-xs font-semibold text-coffee-500 uppercase tracking-wider">Grade</th>
                    <th className="px-5 py-3.5 text-right text-xs font-semibold text-coffee-500 uppercase tracking-wider">Harga</th>
                    <th className="px-5 py-3.5 text-center text-xs font-semibold text-coffee-500 uppercase tracking-wider">Gambar</th>
                    <th className="px-5 py-3.5 text-center text-xs font-semibold text-coffee-500 uppercase tracking-wider">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((item, idx) => (
                    <tr key={item.id} className="table-row-hover border-b border-coffee-50">
                      <td className="px-5 py-3.5 text-sm text-coffee-700">{formatDate(item.created_at)}</td>
                      <td className="px-5 py-3.5 text-sm text-coffee-700 font-medium">{item.weight_gram}g</td>
                      <td className="px-5 py-3.5 text-center">
                        <span className="text-sm font-semibold text-coffee-800">{item.total_defects}</span>
                        <span className="text-xs text-coffee-400 ml-1">(nilai {item.defects_per_350g?.toFixed(1)}/300g)</span>
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <span
                          className="badge font-bold text-white px-3 py-0.5"
                          style={{ backgroundColor: GRADE_COLORS[item.grade_code] || DEFAULT_GRADE_COLOR }}
                        >
                          {item.grade_name}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right text-sm font-semibold text-coffee-800">
                        {formatRupiah(item.total_price)}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        {item.result_image_path ? (
                          <button
                            onClick={() => setPreviewImg(resolveAssetUrl(item.result_image_path))}
                            className="hover:opacity-80 transition-opacity"
                            aria-label={`Lihat gambar hasil analisa ${item.grade_name}`}
                          >
                            <img src={resolveAssetUrl(item.result_image_path)} alt={`Hasil deteksi ${item.grade_name}`} className="w-12 h-12 object-cover rounded-lg mx-auto shadow-sm" />
                          </button>
                        ) : (
                          <ImageOff size={20} className="text-coffee-300 mx-auto" aria-label="Tidak ada gambar" />
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <button onClick={() => handleDelete(item.id)} className="btn-ghost text-red-500 hover:bg-red-50" aria-label="Hapus data analisa">
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-coffee-100 bg-coffee-50/30">
                <p className="text-xs text-coffee-500">
                  Halaman {page} dari {totalPages}
                </p>
                <div className="flex gap-1">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-ghost text-sm disabled:opacity-40"
                  >
                    <ChevronLeft size={16} /> Sebelumnya
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn-ghost text-sm disabled:opacity-40"
                  >
                    Berikutnya <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Image Preview Modal */}
      {previewImg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 animate-fade-in" onClick={() => setPreviewImg(null)}>
          <div className="absolute inset-0 bg-coffee-950/60 backdrop-blur-sm" />
          <div className="relative max-w-3xl w-full animate-scale-in" onClick={e => e.stopPropagation()}>
            <button
              onClick={() => setPreviewImg(null)}
              className="absolute -top-3 -right-3 p-2 bg-white rounded-xl shadow-elevated hover:bg-coffee-50 transition-colors z-10"
            >
              <X size={18} className="text-coffee-600" />
            </button>
            <img src={previewImg} alt="Preview" className="w-full rounded-2xl shadow-elevated" />
          </div>
        </div>
      )}
    </div>
  )
}
