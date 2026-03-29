import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'
import Home from './pages/Home'
import AgentDashboard from './pages/AgentDashboard'
import ConfigPanel from './pages/ConfigPanel'
import Chat from './pages/Chat'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-[#1a1a2e] text-gray-200 overflow-hidden">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <TopBar />
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/agents" element={<AgentDashboard />} />
              <Route path="/config" element={<ConfigPanel />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </main>
        </div>
      </div>
      <Toaster position="bottom-center" theme="dark" />
    </BrowserRouter>
  )
}
