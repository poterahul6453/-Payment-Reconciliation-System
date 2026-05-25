import { useState } from 'react'
import { uploadFile, loadSampleData, runReconcileSync } from '../api/client'

const uploads = [
  { key: 'transactions', endpoint: '/upload/transactions', label: 'Transactions CSV' },
  { key: 'settlements', endpoint: '/upload/settlements', label: 'Settlements CSV' },
  { key: 'refunds', endpoint: '/upload/refunds', label: 'Refunds CSV' },
]

export default function UploadCenter() {
  const [status, setStatus] = useState({})
  const [reconcileResult, setReconcileResult] = useState(null)
  const [busy, setBusy] = useState(false)

  const handleUpload = async (endpoint, file) => {
    setBusy(true)
    try {
      const res = await uploadFile(endpoint, file)
      setStatus((s) => ({ ...s, [endpoint]: res.data.message }))
    } catch (e) {
      setStatus((s) => ({ ...s, [endpoint]: e.response?.data?.detail || e.message }))
    } finally {
      setBusy(false)
    }
  }

  const handleSample = async () => {
    setBusy(true)
    try {
      const res = await loadSampleData()
      setStatus({ sample: res.data.message })
    } catch (e) {
      setStatus({ sample: e.response?.data?.detail || e.message })
    } finally {
      setBusy(false)
    }
  }

  const handleReconcile = async () => {
    setBusy(true)
    try {
      const res = await runReconcileSync()
      setReconcileResult(res.data)
    } catch (e) {
      setReconcileResult({ error: e.response?.data?.detail || e.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="font-medium text-white mb-4">Quick Start</h3>
        <div className="flex gap-3">
          <button
            onClick={handleSample}
            disabled={busy}
            className="px-4 py-2 bg-fintech-accent rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50"
          >
            Load Sample Data
          </button>
          <button
            onClick={handleReconcile}
            disabled={busy}
            className="px-4 py-2 bg-fintech-success rounded-lg text-sm font-medium hover:bg-emerald-600 disabled:opacity-50"
          >
            Run Reconciliation
          </button>
        </div>
        {status.sample && <p className="mt-3 text-sm text-slate-400">{status.sample}</p>}
        {reconcileResult && (
          <pre className="mt-4 p-4 bg-slate-950 rounded-lg text-xs text-slate-300 overflow-auto">
            {JSON.stringify(reconcileResult, null, 2)}
          </pre>
        )}
      </div>

      {uploads.map(({ endpoint, label }) => (
        <div key={endpoint} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="font-medium text-white mb-2">{label}</h3>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => e.target.files[0] && handleUpload(endpoint, e.target.files[0])}
            className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-slate-800 file:text-white"
          />
          {status[endpoint] && <p className="mt-2 text-sm text-slate-400">{status[endpoint]}</p>}
        </div>
      ))}
    </div>
  )
}
