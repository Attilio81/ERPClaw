import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'

export function TeamNode({ data, selected }: NodeProps) {
  const d = data as { name: string; thinking: boolean; num_history_runs: number; tools: string[]; members: string[] }
  return (
    <div className={`min-w-[200px] max-w-[280px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#e94560]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#e94560' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #e94560, #c22d4b)' }}>
        <span className="text-xl">👥</span>
        <span className="font-semibold text-sm text-white truncate">{d.name}</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div>{d.members?.length ?? 0} membri · thinking: {d.thinking ? 'sì' : 'no'}</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {d.tools?.map(t => (
            <span key={t} className="bg-[#0f3460] text-[#7eb8f7] px-1.5 py-0.5 rounded text-[10px]">{t}</span>
          ))}
        </div>
        <div className="mt-1 text-[#888]">{d.num_history_runs} history runs</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#e94560' }} />
    </div>
  )
}
