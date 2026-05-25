import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

export const uploadFile = (endpoint, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(endpoint, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
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
