import { useEffect, useState } from 'react'
import { getDashboardSummary } from '../api/client'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function Reports() {
  const [report, setReport] = useState(null)

  useEffect(() => {
    getDashboardSummary().then((r) => setReport(r.data.latest_report)).catch(console.error)
  }, [])

  if (!report) {
    return (
      <p className="text-slate-400">
        No reports yet. Load sample data, run reconciliation, then refresh.
      </p>
    )
  }

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
        <div className="flex flex-wrap gap-3">
          <a
            href={`${API}/export/report/json?report_id=${report.report_id}`}
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700"
            download
          >
            Download JSON
          </a>
          <a
            href={`${API}/export/report/csv?report_type=mismatch&report_id=${report.report_id}`}
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700"
            download
          >
            Mismatch CSV
          </a>
          <a
            href={`${API}/export/report/csv?report_type=duplicate&report_id=${report.report_id}`}
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700"
            download
          >
            Duplicate CSV
          </a>
          <a
            href={`${API}/export/report/csv?report_type=orphan&report_id=${report.report_id}`}
            className="px-4 py-2 bg-slate-800 rounded-lg text-sm hover:bg-slate-700"
            download
          >
            Orphan Refund CSV
          </a>
        </div>
      </div>
    </div>
  )
}
