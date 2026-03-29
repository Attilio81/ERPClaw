import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'

export function ToolNode({ data, selected }: NodeProps) {
  const d = data as { label: string; description: string; methods: string[] }
  return (
    <div className={`min-w-[180px] max-w-[260px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#1a4a8a]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#1a4a8a' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #0f3460, #1a4a8a)' }}>
        <span className="text-xl">🔧</span>
        <span className="font-semibold text-sm text-white truncate">{d.label}</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div className="truncate">{d.description}</div>
        <div className="mt-1 text-[#7eb8f7]">{d.methods?.length ?? 0} metodi</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#1a4a8a' }} />
    </div>
  )
}
