import { useState, useEffect } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetFooter } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { AgentConfig } from '@/lib/types'

interface NodeEditSheetProps {
  nodeId: string | null
  config: AgentConfig
  onClose: () => void
  onSave: (updated: AgentConfig) => void
}

export function NodeEditSheet({ nodeId, config, onClose, onSave }: NodeEditSheetProps) {
  const [draft, setDraft] = useState<AgentConfig>(config)

  useEffect(() => {
    setDraft(config)
  }, [config, nodeId])

  if (!nodeId) return null

  function set(path: string[], value: unknown) {
    setDraft(prev => {
      const next = structuredClone(prev) as unknown as Record<string, unknown>
      let cur = next
      for (let i = 0; i < path.length - 1; i++) {
        cur = cur[path[i]] as Record<string, unknown>
      }
      cur[path[path.length - 1]] = value
      return next as unknown as AgentConfig
    })
  }

  function handleSave() {
    onSave(draft)
    onClose()
  }

  let title = ''
  let body: React.ReactNode = null

  if (nodeId === 'team') {
    const t = draft.team
    title = `Team: ${t.name}`
    body = (
      <div className="space-y-4">
        <div>
          <Label>Nome</Label>
          <Input value={t.name} onChange={e => set(['team', 'name'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Thinking</Label>
          <Select value={String(t.thinking)} onValueChange={v => set(['team', 'thinking'], v === 'true')}>
            <SelectTrigger className="bg-[#1a1a2e] border-[#0f3460] mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="true">Sì</SelectItem>
              <SelectItem value="false">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>History Runs</Label>
          <Input type="number" min={0} max={20} value={t.num_history_runs}
            onChange={e => set(['team', 'num_history_runs'], parseInt(e.target.value) || 0)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Instructions</Label>
          <Textarea value={t.instructions} rows={10}
            onChange={e => set(['team', 'instructions'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1 font-mono text-xs" />
        </div>
      </div>
    )
  } else if (nodeId === 'memory_manager') {
    const m = draft.memory_manager
    title = 'Memory Manager'
    body = (
      <div>
        <Label>Memory Capture Instructions</Label>
        <Textarea value={m.memory_capture_instructions} rows={10}
          onChange={e => set(['memory_manager', 'memory_capture_instructions'], e.target.value)}
          className="bg-[#1a1a2e] border-[#0f3460] mt-1 font-mono text-xs" />
      </div>
    )
  } else if (nodeId.startsWith('agent:')) {
    const key = nodeId.split(':')[1]
    const a = draft.agents[key]
    if (!a) return null
    title = `Agente: ${a.name}`
    body = (
      <div className="space-y-4">
        <div>
          <Label>Nome</Label>
          <Input value={a.name} onChange={e => set(['agents', key, 'name'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Ruolo</Label>
          <Input value={a.role} onChange={e => set(['agents', key, 'role'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Thinking</Label>
          <Select value={String(a.thinking)} onValueChange={v => set(['agents', key, 'thinking'], v === 'true')}>
            <SelectTrigger className="bg-[#1a1a2e] border-[#0f3460] mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="true">Sì</SelectItem>
              <SelectItem value="false">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Instructions</Label>
          <Textarea value={a.instructions} rows={10}
            onChange={e => set(['agents', key, 'instructions'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1 font-mono text-xs" />
        </div>
      </div>
    )
  } else if (nodeId.startsWith('tool:')) {
    const key = nodeId.split(':')[1]
    const t = draft.tools[key]
    if (!t) return null
    title = `Tool: ${t.label}`
    body = (
      <div className="space-y-4">
        <div>
          <Label>Label</Label>
          <Input value={t.label} onChange={e => set(['tools', key, 'label'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Descrizione</Label>
          <Input value={t.description} onChange={e => set(['tools', key, 'description'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label className="text-xs text-gray-400">Metodi ({t.methods.length}) — sola lettura</Label>
          <div className="flex flex-wrap gap-1 mt-2">
            {t.methods.map(m => (
              <span key={m} className="bg-[#0f3460] text-[#7eb8f7] px-2 py-0.5 rounded text-xs">{m}</span>
            ))}
          </div>
        </div>
      </div>
    )
  } else {
    return null
  }

  return (
    <Sheet open={!!nodeId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="bg-[#16213e] border-[#0f3460] text-gray-200 w-[480px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-gray-200">✏️ {title}</SheetTitle>
        </SheetHeader>
        <div className="mt-6">{body}</div>
        <SheetFooter className="mt-6 flex gap-2">
          <Button variant="outline" onClick={onClose}
            className="flex-1 border-[#0f3460] text-gray-400">Annulla</Button>
          <Button onClick={handleSave}
            className="flex-1 bg-[#533483] hover:bg-[#7b2d8e] border-none">Applica</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
