import axios from 'axios'

export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(
  /\/+$/,
  '',
)

export const api = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
})

export const uploadFile = (endpoint, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(endpoint, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function buildApiUrl(path, params = {}) {
  const url = new URL(path.startsWith('/') ? path : `/${path}`, `${apiBaseUrl}/`)
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== '') url.searchParams.set(key, value)
  })
  return url.toString()
}

export async function downloadExport(path, params, filename) {
  const res = await fetch(buildApiUrl(path, params))
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail || `Download failed (${res.status})`)
  }
  const blob = await res.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

export const loadSampleData = () => api.post('/upload/sample-data')
export const runReconcile = () => api.post('/reconcile/run')
export const runReconcileSync = () => api.post('/reconcile/run-sync')
export const getReport = (id) => api.get(`/reconcile/report/${id}`)
export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getMismatchTrends = () => api.get('/dashboard/mismatch-trends')
export const getSettlementDelays = () => api.get('/dashboard/settlement-delays')
export const getDuplicates = () => api.get('/dashboard/duplicates')
export const getOrphanRefunds = () => api.get('/dashboard/orphan-refunds')
export const getDailyTrend = () => api.get('/dashboard/daily-trend')
export const getMonthlyAnalytics = () => api.get('/dashboard/monthly-analytics')
