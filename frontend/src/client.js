/**
 * API client untuk komunikasi dengan backend FastAPI.
 * Vite proxy otomatis forward /api/* dan /uploads/* ke localhost:8000.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

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