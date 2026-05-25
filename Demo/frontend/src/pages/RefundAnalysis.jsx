import { useEffect, useState } from 'react'
import { getOrphanRefunds } from '../api/client'

export default function RefundAnalysis() {
  const [orphans, setOrphans] = useState([])

  useEffect(() => {
    getOrphanRefunds().then((r) => setOrphans(r.data)).catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <p className="text-slate-400 text-sm">
        Orphan refunds reference transaction IDs that do not exist in the transaction ledger.
      </p>
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 text-slate-400">
            <tr>
              <th className="text-left p-3">Refund ID</th>
              <th className="text-left p-3">Txn ID (missing)</th>
              <th className="text-right p-3">Amount</th>
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Detail</th>
            </tr>
          </thead>
          <tbody>
            {orphans.map((r, i) => (
              <tr key={i} className="border-t border-slate-800">
                <td className="p-3 font-mono">{r.refund_id}</td>
                <td className="p-3 font-mono text-fintech-danger">{r.txn_id}</td>
                <td className="p-3 text-right">${r.refund_amount?.toFixed?.(2) ?? r.refund_amount}</td>
                <td className="p-3 text-slate-400">{r.refund_date}</td>
                <td className="p-3 text-slate-400">{r.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {orphans.length === 0 && (
          <p className="p-8 text-center text-slate-500">No orphan refunds found.</p>
        )}
      </div>
    </div>
  )
}
