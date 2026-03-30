import type { AgentConfig, ChatMessage, EnvConfig, CrmEvent, CrmNote } from './types'

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

export const crmApi = {
  getClienti: () =>
    apiFetch<{ id: number; ragione_sociale: string }[]>('/crm/api/clienti'),

  getMonthEvents: (anno: number, mese: number) =>
    apiFetch<CrmEvent[]>(`/crm/api/eventi?anno=${anno}&mese=${mese}`),

  getEvent: (id: number) =>
    apiFetch<CrmEvent>(`/crm/api/eventi/${id}`),

  createEvent: (data: { tipo: string; data_ora: string; cliente_id?: number; luogo?: string; note?: string; durata_minuti?: number }) =>
    apiFetch<CrmEvent>('/crm/api/eventi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateEvent: (id: number, data: Partial<CrmEvent>) =>
    apiFetch<CrmEvent>(`/crm/api/eventi/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteEvent: (id: number) =>
    apiFetch<{ ok: boolean }>(`/crm/api/eventi/${id}`, { method: 'DELETE' }),

  getClienteStorico: (clienteId: number) =>
    apiFetch<{ eventi: CrmEvent[]; note: CrmNote[] }>(`/crm/api/clienti/${clienteId}/storico`),

  addNota: (clienteId: number, testo: string) =>
    apiFetch<CrmNote>(`/crm/api/clienti/${clienteId}/note`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ testo }),
    }),
}
