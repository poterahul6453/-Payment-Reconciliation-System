import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  LineChart, Line, CartesianGrid, ResponsiveContainer,
} from 'recharts'
import StatCard from '../components/StatCard'
import {
  getDashboardSummary, getMismatchTrends, getSettlementDelays,
  getDailyTrend, getMonthlyAnalytics, getDuplicates,
} from '../api/client'

const COLORS = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [mismatches, setMismatches] = useState([])
  const [delays, setDelays] = useState([])
  const [daily, setDaily] = useState([])
  const [monthly, setMonthly] = useState([])
  const [dupTrend, setDupTrend] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      getMismatchTrends(),
      getSettlementDelays(),
      getDailyTrend(),
      getMonthlyAnalytics(),
      getDuplicates(),
    ])
      .then(([s, m, d, dailyRes, monthlyRes, dup]) => {
        setSummary(s.data)
        setMismatches(m.data)
        setDelays(d.data)
        setDaily(dailyRes.data)
        setMonthly(monthlyRes.data)
        setDupTrend(dup.data.map((x, i) => ({ name: x.txn_id?.slice(0, 12) || `D${i}`, count: x.count || 1 })))
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-400">Loading dashboard...</p>
  if (!summary) return <p className="text-slate-400">No data. Upload sample data and run reconciliation.</p>

  const pie = summary.matched_vs_mismatched || []
  const health = summary.reconciliation_health_score ?? 0

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard label="Transactions" value={summary.total_transactions} />
        <StatCard label="Settlements" value={summary.total_settlements} />
        <StatCard label="Matched" value={summary.matched_count} color="success" />
        <StatCard label="Mismatches" value={summary.mismatch_count} color="danger" />
        <StatCard label="Duplicates" value={summary.duplicate_count} color="warning" />
        <StatCard label="Health Score" value={`${health}%`} sub="Reconciliation health" color={health > 80 ? 'success' : 'warning'} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Matched vs Mismatched</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                {pie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Mismatch Categories</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={mismatches}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="category" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-25} textAnchor="end" height={70} />
              <YAxis tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Settlement Delays (days)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={delays}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="txn_id" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Line type="monotone" dataKey="delay_days" stroke="#f59e0b" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Daily Reconciliation Trend</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Line type="monotone" dataKey="matched" stroke="#10b981" name="Matched" />
              <Line type="monotone" dataKey="mismatched" stroke="#ef4444" name="Mismatched" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Monthly Reconciliation Analytics</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8' }} />
              <YAxis tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Bar dataKey="matched" fill="#10b981" name="Matched" />
              <Bar dataKey="mismatched" fill="#ef4444" name="Mismatched" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Duplicate Settlement Trends</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dupTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
