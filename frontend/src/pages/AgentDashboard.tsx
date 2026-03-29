import { useCallback, useEffect, useState } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState,
  Controls, MiniMap, Background, BackgroundVariant,
} from '@xyflow/react'
import type { NodeTypes, Node, Edge } from '@xyflow/react'
import { toast } from 'sonner'
import { Save, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { TeamNode }   from '@/components/agents/TeamNode'
import { AgentNode }  from '@/components/agents/AgentNode'
import { ToolNode }   from '@/components/agents/ToolNode'
import { MemoryNode } from '@/components/agents/MemoryNode'
import { NodeEditSheet } from '@/components/agents/NodeEditSheet'
import { configToFlow, extractPositions } from '@/components/agents/flowUtils'
import { agentApi } from '@/lib/api'
import type { AgentConfig } from '@/lib/types'

const NODE_TYPES: NodeTypes = {
  teamNode:   TeamNode,
  agentNode:  AgentNode,
  toolNode:   ToolNode,
  memoryNode: MemoryNode,
}

export default function AgentDashboard() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [editNodeId, setEditNodeId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    agentApi.getConfig()
      .then(cfg => {
        setConfig(cfg)
        const { nodes: n, edges: e } = configToFlow(cfg)
        setNodes(n)
        setEdges(e)
      })
      .catch(() => toast.error('Errore caricamento configurazione agenti'))
  }, [])

  const handleNodeDoubleClick = useCallback((_: React.MouseEvent, node: Node) => {
    setEditNodeId(node.id)
  }, [])

  async function handleSave() {
    if (!config) return
    setSaving(true)
    try {
      const positions = extractPositions(nodes)
      const updated: AgentConfig = structuredClone(config)
      if (positions['team']) updated.team.position = positions['team']
      if (positions['memory_manager']) updated.memory_manager.position = positions['memory_manager']
      for (const [id, pos] of Object.entries(positions)) {
        if (id.startsWith('agent:')) {
          const key = id.split(':')[1]
          if (updated.agents[key]) updated.agents[key].position = pos
        } else if (id.startsWith('tool:')) {
          const key = id.split(':')[1]
          if (updated.tools[key]) updated.tools[key].position = pos
        }
      }
      const saved = await agentApi.updateConfig(updated)
      setConfig(saved)
      toast.success('Configurazione salvata su disco')
    } catch {
      toast.error('Errore durante il salvataggio')
    } finally {
      setSaving(false)
    }
  }

  async function handleReload() {
    try {
      await agentApi.reload()
      toast.success('Agenti ricaricati')
    } catch {
      toast.error('Errore ricarica agenti')
    }
  }

  function handleSheetSave(updated: AgentConfig) {
    setConfig(updated)
    const { nodes: n, edges: e } = configToFlow(updated)
    setNodes(prev => n.map(newNode => {
      const existing = prev.find(p => p.id === newNode.id)
      return existing ? { ...newNode, position: existing.position } : newNode
    }))
    setEdges(e)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#16213e] border-b border-[#0f3460]">
        <Button onClick={handleSave} disabled={saving || !config} size="sm"
          className="bg-[#1b6b3a] hover:bg-[#2a9d5c] border-none">
          <Save size={14} className="mr-1" />
          {saving ? 'Salvataggio…' : 'Salva'}
        </Button>
        <Button onClick={handleReload} disabled={!config} size="sm" variant="outline"
          className="border-[#7b2d8e] text-[#7b2d8e] hover:bg-[#533483] hover:text-white">
          <RefreshCw size={14} className="mr-1" />
          Ricarica Agenti
        </Button>
        <span className="text-xs text-gray-500 ml-2">Doppio click su un nodo per modificarlo</span>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeDoubleClick={handleNodeDoubleClick}
          nodeTypes={NODE_TYPES}
          fitView
          colorMode="dark"
        >
          <Controls />
          <MiniMap nodeColor={(node) => {
            if (node.type === 'teamNode')   return '#e94560'
            if (node.type === 'agentNode')  return '#7b2d8e'
            if (node.type === 'toolNode')   return '#1a4a8a'
            if (node.type === 'memoryNode') return '#2a9d5c'
            return '#888'
          }} />
          <Background variant={BackgroundVariant.Dots} gap={24} color="#1e2749" />
        </ReactFlow>
      </div>

      {config && (
        <NodeEditSheet
          nodeId={editNodeId}
          config={config}
          onClose={() => setEditNodeId(null)}
          onSave={handleSheetSave}
        />
      )}
    </div>
  )
}
