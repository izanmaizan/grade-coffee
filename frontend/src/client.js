/**
 * API client untuk komunikasi dengan backend FastAPI.
 *
 * Base URL diambil dari VITE_API_BASE_URL (#17). Default '/api/v1' agar
 * di-proxy oleh Vite saat development. Untuk production, set
 * VITE_API_BASE_URL ke domain backend (mis. https://api.domain.com/api/v1).
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

/**
 * Resolusi URL aset (gambar hasil) agar tetap benar saat backend berada di
 * domain terpisah pada production (#17, #22). Set VITE_UPLOADS_BASE_URL ke
 * origin backend (mis. https://api.domain.com) bila perlu.
 */
const UPLOADS_BASE_URL = import.meta.env.VITE_UPLOADS_BASE_URL || ''
export const resolveAssetUrl = (path) => {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  return `${UPLOADS_BASE_URL}${path}`
}

export const pricesApi = {
  list: () => api.get('/prices').then(r => r.data),
  get: (id) => api.get(`/prices/${id}`).then(r => r.data),
  create: (data) => api.post('/prices', data).then(r => r.data),
  update: (id, data) => api.put(`/prices/${id}`, data).then(r => r.data),
  remove: (id) => api.delete(`/prices/${id}`),
}

export const analyzeApi = {
  analyze: (file, weightGram) => {
    const fd = new FormData()
    fd.append('image', file)
    fd.append('weight_gram', String(weightGram))
    return api.post('/analyze', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  status: () => api.get('/analyze/status').then(r => r.data),
  reload: () => api.post('/analyze/reload-model').then(r => r.data),
}

export const historyApi = {
  list: (page = 1, pageSize = 20, gradeCode = null) => {
    const params = { page, page_size: pageSize }
    if (gradeCode) params.grade_code = gradeCode
    return api.get('/history', { params }).then(r => r.data)
  },
  get: (id) => api.get(`/history/${id}`).then(r => r.data),
  remove: (id) => api.delete(`/history/${id}`),
  stats: () => api.get('/history/stats/summary').then(r => r.data),
}

export const formatRupiah = (value) => {
  if (value == null || isNaN(value)) return 'Rp 0'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export const formatRupiahDetail = (value) => {
  if (value == null || isNaN(value)) return 'Rp 0'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export const formatDate = (isoString) => {
  if (!isoString) return '-'
  const d = new Date(isoString)
  return d.toLocaleDateString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default api