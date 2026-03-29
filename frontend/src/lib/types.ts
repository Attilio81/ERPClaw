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
