import { useEffect, useState } from 'react'
import { getDashboardSummary } from '../api/client'
import { api } from '../api/client'

export default function MismatchExplorer() {
  const [mismatches, setMismatches] = useState([])
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    getDashboardSummary()
      .then(async (s) => {
        const id = s.data.latest_report?.report_id
        if (!id) return
        const res = await api.get(`/reconcile/report/${id}`)
        setMismatches(res.data.mismatches || [])
      })
      .catch(console.error)
  }, [])

  const categories = [...new Set(mismatches.map((m) => m.category))]
  const filtered = filter === 'all' ? mismatches : mismatches.filter((m) => m.category === filter)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded-lg text-sm ${filter === 'all' ? 'bg-fintech-accent' : 'bg-slate-800'}`}
        >
          All ({mismatches.length})
        </button>
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={`px-3 py-1 rounded-lg text-sm ${filter === c ? 'bg-fintech-accent' : 'bg-slate-800'}`}
          >
            {c} ({mismatches.filter((m) => m.category === c).length})
          </button>
        ))}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 text-slate-400">
            <tr>
              <th className="text-left p-3">Category</th>
              <th className="text-left p-3">Txn ID</th>
              <th className="text-left p-3">Settlement ID</th>
              <th className="text-right p-3">Expected</th>
              <th className="text-right p-3">Actual</th>
              <th className="text-left p-3">Detail</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m, i) => (
              <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/50">
                <td className="p-3"><span className="px-2 py-0.5 rounded bg-slate-800 text-xs">{m.category}</span></td>
                <td className="p-3 font-mono text-xs">{m.txn_id || '—'}</td>
                <td className="p-3 font-mono text-xs">{m.settlement_id || '—'}</td>
                <td className="p-3 text-right">{m.expected_amount ?? '—'}</td>
                <td className="p-3 text-right">{m.actual_amount ?? '—'}</td>
                <td className="p-3 text-slate-400">{m.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="p-8 text-center text-slate-500">No mismatches. Run reconciliation first.</p>
        )}
      </div>
    </div>
  )
}
