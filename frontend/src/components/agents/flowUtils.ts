import type { Node, Edge } from '@xyflow/react'
import type { AgentConfig } from '@/lib/types'

export function configToFlow(config: AgentConfig): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  nodes.push({
    id: 'memory_manager',
    type: 'memoryNode',
    position: config.memory_manager.position,
    data: { ...config.memory_manager },
  })

  nodes.push({
    id: 'team',
    type: 'teamNode',
    position: config.team.position,
    data: { ...config.team },
  })

  edges.push({
    id: 'memory-team',
    source: 'memory_manager',
    target: 'team',
    animated: true,
    style: { stroke: '#2a9d5c', strokeWidth: 2 },
  })

  for (const [key, agent] of Object.entries(config.agents)) {
    nodes.push({
      id: `agent:${key}`,
      type: 'agentNode',
      position: agent.position,
      data: { ...agent, _key: key },
    })
    if (config.team.members.includes(key)) {
      edges.push({
        id: `team-agent:${key}`,
        source: 'team',
        target: `agent:${key}`,
        animated: true,
        style: { stroke: '#e94560', strokeWidth: 2 },
      })
    }
  }

  for (const [key, tool] of Object.entries(config.tools)) {
    nodes.push({
      id: `tool:${key}`,
      type: 'toolNode',
      position: tool.position,
      data: { ...tool, _key: key },
    })
    if (config.team.tools.includes(key)) {
      edges.push({
        id: `tool:${key}-team`,
        source: `tool:${key}`,
        target: 'team',
        animated: true,
        style: { stroke: '#1a4a8a', strokeWidth: 2 },
      })
    }
    for (const [agentKey, agent] of Object.entries(config.agents)) {
      if (agent.tools.includes(key)) {
        edges.push({
          id: `tool:${key}-agent:${agentKey}`,
          source: `tool:${key}`,
          target: `agent:${agentKey}`,
          animated: true,
          style: { stroke: '#7b2d8e', strokeWidth: 2 },
        })
      }
    }
  }

  return { nodes, edges }
}

export function extractPositions(nodes: Node[]): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {}
  for (const node of nodes) {
    positions[node.id] = node.position
  }
  return positions
}
