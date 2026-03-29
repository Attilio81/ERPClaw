import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'

export function AgentNode({ data, selected }: NodeProps) {
  const d = data as { name: string; role: string; thinking: boolean; tools: string[] }
  return (
    <div className={`min-w-[200px] max-w-[280px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#7b2d8e]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#7b2d8e' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #533483, #7b2d8e)' }}>
        <span className="text-xl">🤖</span>
        <span className="font-semibold text-sm text-white truncate">{d.name}</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div className="truncate">{d.role}</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {d.tools?.map(t => (
            <span key={t} className="bg-[#0f3460] text-[#7eb8f7] px-1.5 py-0.5 rounded text-[10px]">{t}</span>
          ))}
        </div>
        <div className="mt-1 text-[#888]">thinking: {d.thinking ? 'sì' : 'no'}</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#7b2d8e' }} />
    </div>
  )
}
