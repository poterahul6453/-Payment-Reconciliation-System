export default function StatCard({ label, value, sub, color = 'accent' }) {
  const colors = {
    accent: 'text-fintech-accent',
    success: 'text-fintech-success',
    warning: 'text-fintech-warning',
    danger: 'text-fintech-danger',
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${colors[color]}`}>{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}
