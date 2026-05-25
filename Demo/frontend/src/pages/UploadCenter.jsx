import { useState } from 'react'
import {
  uploadFile,
  loadSampleData,
  runReconcileSync,
  downloadSampleCsv,
  downloadSampleTemplate,
  downloadAllSampleCsv,
} from '../api/client'

const uploads = [
  {
    key: 'transactions',
    endpoint: '/upload/transactions',
    label: 'Transactions CSV',
    hint: 'txn_id, customer_id, order_id, amount, payment_status, …',
  },
  {
    key: 'settlements',
    endpoint: '/upload/settlements',
    label: 'Settlements CSV',
    hint: 'settlement_id, txn_id, settled_amount, settlement_status, …',
  },
  {
    key: 'refunds',
    endpoint: '/upload/refunds',
    label: 'Refunds CSV',
    hint: 'refund_id, txn_id, refund_amount, refund_date',
  },
]

export default function UploadCenter() {
  const [status, setStatus] = useState({})
  const [reconcileResult, setReconcileResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [downloading, setDownloading] = useState(null)

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

  const handleDownload = async (id, fn) => {
    setDownloading(id)
    try {
      await fn()
    } catch (e) {
      setStatus((s) => ({ ...s, download: e.message || 'Download failed' }))
    } finally {
      setDownloading(null)
    }
  }

  const downloadDisabled = busy || !!downloading

  return (
    <div className="max-w-2xl space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="font-medium text-white mb-2">Quick Start</h3>
        <p className="text-sm text-slate-400 mb-4">
          Load demo data into the database, or download sample CSVs below, edit them, and upload each
          section.
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleSample}
            disabled={busy}
            className="px-4 py-2 bg-fintech-accent rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50"
          >
            Load Sample Data
          </button>
          <button
            type="button"
            onClick={handleReconcile}
            disabled={busy}
            className="px-4 py-2 bg-fintech-success rounded-lg text-sm font-medium hover:bg-emerald-600 disabled:opacity-50"
          >
            Run Reconciliation
          </button>
          <button
            type="button"
            onClick={() => handleDownload('all', downloadAllSampleCsv)}
            disabled={downloadDisabled}
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            {downloading === 'all' ? 'Downloading…' : 'Download all sample CSVs (zip)'}
          </button>
        </div>
        {status.sample && <p className="mt-3 text-sm text-slate-400">{status.sample}</p>}
        {status.download && <p className="mt-3 text-sm text-fintech-danger">{status.download}</p>}
        {reconcileResult && (
          <pre className="mt-4 p-4 bg-slate-950 rounded-lg text-xs text-slate-300 overflow-auto">
            {JSON.stringify(reconcileResult, null, 2)}
          </pre>
        )}
      </div>

      {uploads.map(({ key, endpoint, label, hint }) => (
        <div key={endpoint} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="font-medium text-white mb-1">{label}</h3>
          <p className="text-xs text-slate-500 mb-4">{hint}</p>
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              type="button"
              onClick={() => handleDownload(`${key}-sample`, () => downloadSampleCsv(key))}
              disabled={downloadDisabled}
              className="px-3 py-1.5 bg-slate-800 rounded-lg text-xs hover:bg-slate-700 disabled:opacity-50"
            >
              {downloading === `${key}-sample` ? 'Downloading…' : 'Download sample CSV'}
            </button>
            <button
              type="button"
              onClick={() => handleDownload(`${key}-template`, () => downloadSampleTemplate(key))}
              disabled={downloadDisabled}
              className="px-3 py-1.5 bg-slate-800 rounded-lg text-xs hover:bg-slate-700 disabled:opacity-50"
            >
              {downloading === `${key}-template` ? 'Downloading…' : 'Download blank template'}
            </button>
          </div>
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
