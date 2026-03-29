import { useLocation } from 'react-router-dom'

const TITLES: Record<string, string> = {
  '/':       'Home',
  '/agents': 'Agent Dashboard',
  '/config': 'Configurazione',
  '/chat':   'Chat',
}

export function TopBar() {
  const { pathname } = useLocation()
  const title = TITLES[pathname] ?? 'ERPClaw'
  return (
    <header className="h-11 bg-[#16213e] border-b border-[#0f3460] flex items-center px-4 shrink-0">
      <h1 className="text-sm font-semibold text-gray-200">{title}</h1>
    </header>
  )
}
