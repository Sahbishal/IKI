import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Upload from './pages/Upload'
import Documents from './pages/Documents'
import KnowledgeGraph from './pages/KnowledgeGraph'
import Reports from './pages/Reports'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-mesh overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/"               element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard"      element={<Dashboard />} />
            <Route path="/chat"           element={<Chat />} />
            <Route path="/upload"         element={<Upload />} />
            <Route path="/documents"      element={<Documents />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
            <Route path="/reports"        element={<Reports />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
