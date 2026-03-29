import { useNavigate } from 'react-router-dom'
import { Bot, Settings, MessageSquare, ExternalLink } from 'lucide-react'

interface NavCard {
  icon: React.ReactNode
  title: string
  description: string
  action: () => void
}

export default function Home() {
  const navigate = useNavigate()

  const cards: NavCard[] = [
    {
      icon: <Bot size={28} className="text-[#e94560]" />,
      title: 'Agent Dashboard',
      description: 'Visualizza e configura il team di agenti AI con editor visivo',
      action: () => navigate('/agents'),
    },
    {
      icon: <Settings size={28} className="text-[#7b2d8e]" />,
      title: 'Configurazione',
      description: "Modifica le variabili d'ambiente (provider LLM, token, chiavi API)",
      action: () => navigate('/config'),
    },
    {
      icon: <MessageSquare size={28} className="text-[#2a9d5c]" />,
      title: 'Chat',
      description: "Invia messaggi all'agente ERP direttamente dal browser",
      action: () => navigate('/chat'),
    },
    {
      icon: <ExternalLink size={28} className="text-[#1a4a8a]" />,
      title: 'Admin DB',
      description: 'Gestisci articoli, clienti, ordini e magazzino via SQLAdmin',
      action: () => window.open(`http://${window.location.hostname}:8000/admin`, '_blank'),
    },
  ]

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">ERPClaw</h2>
        <p className="text-gray-400 text-sm">Mini-ERP gestito da agente AI via Telegram</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {cards.map((card) => (
          <button
            key={card.title}
            onClick={card.action}
            className="bg-[#16213e] border border-[#0f3460] rounded-xl p-6 text-left
                       hover:border-[#1a4a8a] hover:bg-[#1e2a4a] transition-all group"
          >
            <div className="mb-4">{card.icon}</div>
            <h3 className="font-semibold text-white mb-1 group-hover:text-[#7eb8f7] transition-colors">
              {card.title}
            </h3>
            <p className="text-gray-400 text-sm leading-relaxed">{card.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
