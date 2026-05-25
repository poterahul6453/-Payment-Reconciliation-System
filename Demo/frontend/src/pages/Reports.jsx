import { useEffect, useState } from 'react'
import { downloadExport, getDashboardSummary } from '../api/client'

export default function Reports() {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [downloading, setDownloading] = useState(null)

  useEffect(() => {
    getDashboardSummary().then((r) => setReport(r.data.latest_report)).catch(console.error)
  }, [])

  const handleDownload = async (key, path, params, filename) => {
    setError(null)
    setDownloading(key)
    try {
      await downloadExport(path, params, filename)
    } catch (e) {
      setError(e.message || 'Download failed')
    } finally {
      setDownloading(null)
    }
  }

  if (!report) {
    return (
      <p className="text-slate-400">
        No reports yet. Load sample data, run reconciliation, then refresh.
      </p>
    )
  }

  const reportId = report.report_id

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="font-medium text-white mb-4">Latest Report</h3>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-slate-500">Report ID</dt><dd className="font-mono text-slate-300">{report.report_id}</dd></div>
          <div><dt className="text-slate-500">Generated</dt><dd>{new Date(report.generated_at).toLocaleString()}</dd></div>
          <div><dt className="text-slate-500">Matched</dt><dd className="text-fintech-success">{report.matched_count}</dd></div>
          <div><dt className="text-slate-500">Mismatches</dt><dd className="text-fintech-danger">{report.mismatch_count}</dd></div>
          <div><dt className="text-slate-500">Duplicates</dt><dd className="text-fintech-warning">{report.duplicate_count}</dd></div>
          <div><dt className="text-slate-500">Orphan Refunds</dt><dd>{report.orphan_refund_count}</dd></div>
          <div><dt className="text-slate-500">Health Score</dt><dd>{report.reconciliation_health_score}%</dd></div>
        </dl>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="font-medium text-white mb-4">Export Reports</h3>
        {error && <p className="text-fintech-danger text-sm mb-3">{error}</p>}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={!!downloading}
            onClick={() =>
              handleDownload('json', '/export/report/json', { report_id: reportId }, 'reconciliation_report.json')
            }
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            {downloading === 'json' ? 'Downloading…' : 'Download JSON'}
          </button>
          <button
            type="button"
            disabled={!!downloading}
            onClick={() =>
              handleDownload(
                'mismatch',
                '/export/report/csv',
                { report_type: 'mismatch', report_id: reportId },
                'mismatch_report.csv',
              )
            }
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            {downloading === 'mismatch' ? 'Downloading…' : 'Mismatch CSV'}
          </button>
          <button
            type="button"
            disabled={!!downloading}
            onClick={() =>
              handleDownload(
                'duplicate',
                '/export/report/csv',
                { report_type: 'duplicate', report_id: reportId },
                'duplicate_report.csv',
              )
            }
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            {downloading === 'duplicate' ? 'Downloading…' : 'Duplicate CSV'}
          </button>
          <button
            type="button"
            disabled={!!downloading}
            onClick={() =>
              handleDownload(
                'orphan',
                '/export/report/csv',
                { report_type: 'orphan', report_id: reportId },
                'orphan_refund_report.csv',
              )
            }
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            {downloading === 'orphan' ? 'Downloading…' : 'Orphan Refund CSV'}
          </button>
        </div>
      </div>
    </div>
  )
}
