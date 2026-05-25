import { Link, useLocation } from 'react-router-dom'

const nav = [
  { path: '/', label: 'Dashboard' },
  { path: '/upload', label: 'Upload Center' },
  { path: '/reports', label: 'Reports' },
  { path: '/mismatches', label: 'Mismatch Explorer' },
  { path: '/duplicates', label: 'Duplicates' },
  { path: '/refunds', label: 'Refund Analysis' },
]

export default function Layout({ children }) {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-fintech-navy border-r border-slate-800 p-4 flex flex-col">
        <div className="mb-8">
          <h1 className="text-lg font-bold text-white">ReconPay</h1>
          <p className="text-xs text-slate-400">Payment Reconciliation</p>
        </div>
        <nav className="flex-1 space-y-1">
          {nav.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={`block px-3 py-2 rounded-lg text-sm transition ${
                pathname === path
                  ? 'bg-fintech-accent text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <header className="border-b border-slate-800 bg-slate-900/50 px-8 py-4">
          <h2 className="text-xl font-semibold text-white">
            {nav.find((n) => n.path === pathname)?.label || 'Reconciliation'}
          </h2>
        </header>
        <div className="p-8">{children}</div>
      </main>
    </div>
  )
}
