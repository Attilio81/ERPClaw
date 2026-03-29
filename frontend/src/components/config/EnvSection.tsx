import { useState } from 'react'
import { ChevronDown, Eye, EyeOff } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { EnvConfig } from '@/lib/types'

interface Field {
  key: keyof EnvConfig
  label: string
  type?: 'text' | 'password' | 'select'
  options?: string[]
  placeholder?: string
}

interface EnvSectionProps {
  title: string
  fields: Field[]
  values: Partial<EnvConfig>
  onChange: (key: keyof EnvConfig, value: string) => void
}

export function EnvSection({ title, fields, values, onChange }: EnvSectionProps) {
  const [open, setOpen] = useState(true)
  const [showSecrets, setShowSecrets] = useState(false)

  return (
    <div className="bg-[#16213e] border border-[#0f3460] rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold hover:bg-[#1e2a4a] transition-colors"
      >
        {title}
        <ChevronDown size={16} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4">
          {fields.some(f => f.type === 'password') && (
            <button
              type="button"
              onClick={() => setShowSecrets(!showSecrets)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
            >
              {showSecrets ? <EyeOff size={12} /> : <Eye size={12} />}
              {showSecrets ? 'Nascondi valori' : 'Mostra valori'}
            </button>
          )}

          {fields.map((field) => (
            <div key={field.key}>
              <Label className="text-xs text-gray-400 uppercase tracking-wide mb-1 block">
                {field.label}
              </Label>
              {field.type === 'select' ? (
                <Select
                  value={values[field.key] || ''}
                  onValueChange={(v) => onChange(field.key, v ?? '')}
                >
                  <SelectTrigger className="bg-[#1a1a2e] border-[#0f3460]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {field.options?.map(opt => (
                      <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  type={field.type === 'password' && !showSecrets ? 'password' : 'text'}
                  value={values[field.key] || ''}
                  placeholder={field.placeholder}
                  onChange={(e) => onChange(field.key, e.target.value)}
                  className="bg-[#1a1a2e] border-[#0f3460] focus:border-[#533483]"
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
