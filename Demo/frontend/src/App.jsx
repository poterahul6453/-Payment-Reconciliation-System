import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import UploadCenter from './pages/UploadCenter'
import Reports from './pages/Reports'
import MismatchExplorer from './pages/MismatchExplorer'
import Duplicates from './pages/Duplicates'
import RefundAnalysis from './pages/RefundAnalysis'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadCenter />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/mismatches" element={<MismatchExplorer />} />
        <Route path="/duplicates" element={<Duplicates />} />
        <Route path="/refunds" element={<RefundAnalysis />} />
      </Routes>
    </Layout>
  )
}
