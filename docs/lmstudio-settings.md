# LM Studio — Impostazioni consigliate per ERPClaw

## Modello consigliato

**Qwen3.5-9B** in formato GGUF quantizzato.

| Variante GGUF | VRAM richiesta | Qualità |
|---|---|---|
| Q8_0 | ~10 GB | Ottima |
| Q6_K | ~8 GB | Ottima |
| Q4_K_M | ~6 GB | Buona (consigliata se RAM limitata) |
| Q2_K | ~4 GB | Accettabile, tool calling meno affidabile |

---

## Server locale (tab "Local Server")

| Impostazione | Valore | Motivo |
|---|---|---|
| **Port** | `1234` | Default usato in `.env` |
| **Enable CORS** | ✅ On | Necessario per chiamate locali |
| **Serve on local network** | ❌ Off | Sicurezza — solo localhost |
| **Context Length** | `16384` | Sufficiente per conversazioni ERP lunghe |
| **GPU Layers (GPU Offload)** | Massimo possibile | Velocità — scarica tutto su GPU |

---

## Parametri di inferenza (tab "My Models" → impostazioni modello)

### Per uso agente / tool calling

| Parametro | Valore |
|---|---|
| **Temperature** | `0.6` |
| **Top P** | `0.95` |
| **Top K** | `20` |
| **Min P** | `0.0` |
| **Repeat Penalty** | `1.0` |
| **Presence Penalty** | `0.0` |

> Temperatura bassa (0.6) = risposte più deterministiche e JSON più affidabile.

### Thinking mode

| Impostazione | Valore | Note |
|---|---|---|
| **Enable thinking** | ✅ On | Migliora ragionamento multi-step |
| **Thinking budget** | `2048` token | Bilanciamento velocità/qualità |

> Se il tool calling fallisce spesso, prova a disabilitare il thinking e abbassa la temperature a `0.4`.

---

## Structured Output

| Impostazione | Valore | Motivo |
|---|---|---|
| **Structured Output** | ✅ On | Forza JSON valido nelle chiamate tool |

> ⚠️ Su alcuni modelli Structured Output disabilita il thinking. Se noti ragionamenti peggiori, disattivalo — Qwen3.5-9B ha tool calling nativo robusto anche senza.

---

## System Prompt (lasciare vuoto)

LM Studio permette di impostare un system prompt globale nel server.
**Lasciarlo vuoto**: ERPClaw gestisce già le istruzioni tramite agno (`team.instructions`).

---

## Checklist avvio

- [ ] LM Studio aperto con modello caricato
- [ ] Tab "Local Server" → server avviato (pulsante verde)
- [ ] URL server visibile: `http://localhost:1234`
- [ ] `.env` con `LLM_PROVIDER=lmstudio` e `LMSTUDIO_BASE_URL=http://localhost:1234`
- [ ] Avviare ERPClaw con `start.bat`

---

## Troubleshooting

**Tool calling non funziona / JSON malformato**
- Abbassa temperature a `0.4`
- Disabilita thinking mode
- Passa a quantizzazione più alta (Q6_K o Q8_0)

**Risposte lente**
- Aumenta GPU Layers (più layer su GPU = più veloce)
- Riduci Context Length a `8192`
- Usa Q4_K_M invece di Q8_0

**Modello non trovato da agno**
- Verifica che l'ID in LM Studio corrisponda esattamente a `LLM_MODEL_ID` nel `.env`
- L'ID è visibile nella barra in alto di LM Studio quando il modello è caricato
