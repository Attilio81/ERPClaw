import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Save } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EnvSection } from '@/components/config/EnvSection'
import { configApi } from '@/lib/api'
import type { EnvConfig } from '@/lib/types'

const EMPTY: EnvConfig = {
  TELEGRAM_BOT_TOKEN: '', ALLOWED_CHAT_ID: '',
  LLM_PROVIDER: 'lmstudio', LLM_MODEL_ID: '',
  LMSTUDIO_BASE_URL: '', OPENAI_API_KEY: '',
  DEEPSEEK_API_KEY: '', SHOP_SECRET_KEY: '',
}

export default function ConfigPanel() {
  const [values, setValues] = useState<EnvConfig>(EMPTY)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    configApi.get()
      .then(setValues)
      .catch(() => toast.error('Errore caricamento configurazione'))
  }, [])

  function handleChange(key: keyof EnvConfig, value: string) {
    setValues(prev => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    setSaving(true)
    try {
      const saved = await configApi.update(values)
      setValues(saved)
      toast.success('Configurazione salvata')
    } catch {
      toast.error('Errore durante il salvataggio')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-400">Modifica il file <code className="text-[#7eb8f7]">.env</code></p>
        <Button onClick={handleSave} disabled={saving} size="sm"
          className="bg-[#1b6b3a] hover:bg-[#2a9d5c] border-none">
          <Save size={14} className="mr-1" />
          {saving ? 'Salvataggio…' : 'Salva'}
        </Button>
      </div>

      <EnvSection
        title="Telegram"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'TELEGRAM_BOT_TOKEN', label: 'Bot Token', type: 'password', placeholder: '123456:ABC...' },
          { key: 'ALLOWED_CHAT_ID',    label: 'Chat ID',   type: 'text',     placeholder: '12345678' },
        ]}
      />

      <EnvSection
        title="LLM"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'LLM_PROVIDER',      label: 'Provider',         type: 'select', options: ['lmstudio', 'deepseek'] },
          { key: 'LLM_MODEL_ID',      label: 'Model ID',         type: 'text',   placeholder: 'qwen/qwen3.5-9b' },
          { key: 'LMSTUDIO_BASE_URL', label: 'LM Studio URL',    type: 'text',   placeholder: 'http://localhost:1234/v1' },
          { key: 'DEEPSEEK_API_KEY',  label: 'DeepSeek API Key', type: 'password' },
        ]}
      />

      <EnvSection
        title="OpenAI (Whisper)"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'OPENAI_API_KEY', label: 'API Key', type: 'password', placeholder: 'sk-...' },
        ]}
      />

      <EnvSection
        title="Shop"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'SHOP_SECRET_KEY', label: 'Secret Key', type: 'password' },
        ]}
      />
    </div>
  )
}
