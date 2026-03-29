import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'

export function MemoryNode({ data, selected }: NodeProps) {
  const d = data as { memory_capture_instructions: string }
  const preview = (d.memory_capture_instructions || '').slice(0, 60)
  return (
    <div className={`min-w-[180px] max-w-[260px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#2a9d5c]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#2a9d5c' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #1b6b3a, #2a9d5c)' }}>
        <span className="text-xl">🧠</span>
        <span className="font-semibold text-sm text-white">Memory Manager</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div>{preview}{preview.length === 60 ? '…' : ''}</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#2a9d5c' }} />
    </div>
  )
}
