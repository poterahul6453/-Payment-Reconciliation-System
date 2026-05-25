import { useEffect, useState } from 'react'
import { getDuplicates } from '../api/client'

export default function Duplicates() {
  const [items, setItems] = useState([])

  useEffect(() => {
    getDuplicates().then((r) => setItems(r.data)).catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <p className="text-slate-400 text-sm">
        Duplicate settlements occur when the same transaction ID appears in multiple settlement records.
      </p>
      <div className="grid gap-4">
        {items.map((d, i) => (
          <div key={i} className="bg-slate-900 border border-fintech-warning/30 rounded-xl p-5">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-mono text-fintech-warning">{d.txn_id}</p>
                <p className="text-sm text-slate-400 mt-1">{d.count} duplicate settlement(s)</p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(d.settlement_ids || []).map((sid, j) => (
                <span key={j} className="px-2 py-1 bg-slate-800 rounded text-xs font-mono">{sid}</span>
              ))}
            </div>
            <p className="mt-2 text-sm text-slate-500">
              Amounts: {(d.settled_amounts || []).join(', ')}
            </p>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-slate-500 text-center py-12">No duplicate settlements detected.</p>
        )}
      </div>
    </div>
  )
}
