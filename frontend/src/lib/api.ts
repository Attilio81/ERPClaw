import type { AgentConfig, ChatMessage, EnvConfig } from './types'

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

export const agentApi = {
  getConfig: () =>
    apiFetch<AgentConfig>('/agents/api/config'),

  updateConfig: (config: AgentConfig) =>
    apiFetch<AgentConfig>('/agents/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }),

  reload: () =>
    apiFetch<{ status: string; message: string }>('/agents/api/reload', {
      method: 'POST',
    }),
}

export const configApi = {
  get: () =>
    apiFetch<EnvConfig>('/config/api'),

  update: (values: Partial<EnvConfig>) =>
    apiFetch<EnvConfig>('/config/api', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    }),
}

export const chatApi = {
  getHistory: () =>
    apiFetch<ChatMessage[]>('/chat/api/history'),

  send: (message: string) =>
    apiFetch<ChatMessage>('/chat/api/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    }),
}
