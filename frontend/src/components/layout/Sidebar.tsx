import { NavLink } from 'react-router-dom'
import { Home, Bot, Settings, MessageSquare, ExternalLink } from 'lucide-react'

const links = [
  { to: '/',       icon: Home,          label: 'Home',    end: true },
  { to: '/agents', icon: Bot,           label: 'Agenti',  end: false },
  { to: '/config', icon: Settings,      label: 'Config',  end: false },
  { to: '/chat',   icon: MessageSquare, label: 'Chat',    end: false },
]

export function Sidebar() {
  return (
    <nav className="w-14 md:w-52 bg-[#16213e] border-r border-[#0f3460] flex flex-col py-4 shrink-0">
      <div className="px-4 mb-6 hidden md:flex items-center gap-2">
        <span className="text-[#e94560] font-bold text-sm">ERPClaw</span>
      </div>

      <div className="flex flex-col gap-1 px-2">
        {links.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-[#0f3460] text-white'
                  : 'text-gray-400 hover:text-white hover:bg-[#0f3460]/50',
              ].join(' ')
            }
          >
            <Icon size={18} className="shrink-0" />
            <span className="hidden md:inline">{label}</span>
          </NavLink>
        ))}
      </div>

      <div className="mt-auto px-2">
        <a
          href="/admin"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-gray-400 hover:text-white hover:bg-[#0f3460]/50 transition-colors"
        >
          <ExternalLink size={18} className="shrink-0" />
          <span className="hidden md:inline">Admin DB</span>
        </a>
      </div>
    </nav>
  )
}
