export interface Position {
  x: number
  y: number
}

export interface TeamConfig {
  name: string
  thinking: boolean
  num_history_runs: number
  instructions: string
  tools: string[]
  members: string[]
  position: Position
}

export interface AgentNodeConfig {
  name: string
  role: string
  thinking: boolean
  instructions: string
  tools: string[]
  position: Position
}

export interface ToolConfig {
  label: string
  description: string
  methods: string[]
  position: Position
}

export interface MemoryManagerConfig {
  memory_capture_instructions: string
  position: Position
}

export interface AgentConfig {
  team: TeamConfig
  agents: Record<string, AgentNodeConfig>
  tools: Record<string, ToolConfig>
  memory_manager: MemoryManagerConfig
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface EnvConfig {
  TELEGRAM_BOT_TOKEN: string
  ALLOWED_CHAT_ID: string
  LLM_PROVIDER: string
  LLM_MODEL_ID: string
  LMSTUDIO_BASE_URL: string
  OPENAI_API_KEY: string
  DEEPSEEK_API_KEY: string
  SHOP_SECRET_KEY: string
}

export interface CrmEvent {
  id: number
  tipo: 'visita' | 'chiamata' | 'email'
  stato: 'pianificato' | 'completato' | 'annullato'
  data_ora: string
  durata_minuti: number | null
  luogo: string | null
  esito: string | null
  note: string | null
  cliente_id: number | null
  cliente_nome: string | null
  reminder_inviato: boolean
}

export interface CrmNote {
  id: number
  cliente_id: number
  testo: string
  data_ora: string
  autore: string | null
}
