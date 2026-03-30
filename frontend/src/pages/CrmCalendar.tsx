import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Calendar, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { crmApi } from '@/lib/api'
import type { CrmEvent } from '@/lib/types'
import { toast } from 'sonner'

const DAYS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
const MONTHS = [
  'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
  'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre',
]

function eventColor(ev: CrmEvent): string {
  if (ev.stato === 'annullato') return 'bg-gray-500/40 text-gray-400'
  if (ev.stato === 'completato') return 'bg-green-700/70 text-green-200'
  switch (ev.tipo) {
    case 'visita': return 'bg-indigo-700/70 text-indigo-200'
    case 'chiamata': return 'bg-amber-700/70 text-amber-200'
    case 'email': return 'bg-slate-600/70 text-slate-200'
  }
}

function dotColor(ev: CrmEvent): string {
  if (ev.stato === 'annullato') return 'bg-gray-500'
  if (ev.stato === 'completato') return 'bg-green-500'
  switch (ev.tipo) {
    case 'visita': return 'bg-indigo-500'
    case 'chiamata': return 'bg-amber-500'
    case 'email': return 'bg-slate-400'
  }
}

export default function CrmCalendar() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [events, setEvents] = useState<CrmEvent[]>([])
  const [clienti, setClienti] = useState<{ id: number; ragione_sociale: string }[]>([])
  const [sheetOpen, setSheetOpen] = useState(false)
  const [selectedDay, setSelectedDay] = useState<number | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<CrmEvent | null>(null)
  const [newForm, setNewForm] = useState({ tipo: 'visita', data_ora: '', cliente_id: '', luogo: '', note: '' })

  useEffect(() => {
    crmApi.getClienti().then(setClienti).catch(() => {})
  }, [])

  useEffect(() => {
    crmApi.getMonthEvents(year, month)
      .then(setEvents)
      .catch(() => toast.error('Errore nel caricamento eventi'))
  }, [year, month])

  function prevMonth() {
    if (month === 1) { setYear(y => y - 1); setMonth(12) }
    else setMonth(m => m - 1)
  }
  function nextMonth() {
    if (month === 12) { setYear(y => y + 1); setMonth(1) }
    else setMonth(m => m + 1)
  }

  const daysInMonth = new Date(year, month, 0).getDate()
  let startOffset = new Date(year, month - 1, 1).getDay() - 1
  if (startOffset < 0) startOffset = 6

  const totalCells = Math.ceil((startOffset + daysInMonth) / 7) * 7
  const cells = Array.from({ length: totalCells }, (_, i) => {
    const day = i - startOffset + 1
    return day >= 1 && day <= daysInMonth ? day : null
  })

  function eventsForDay(day: number): CrmEvent[] {
    return events.filter(ev => {
      const d = new Date(ev.data_ora)
      return d.getFullYear() === year && d.getMonth() + 1 === month && d.getDate() === day
    })
  }

  function openDay(day: number) {
    setSelectedDay(day)
    setSelectedEvent(null)
    const dayStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}T09:00`
    setNewForm({ tipo: 'visita', data_ora: dayStr, cliente_id: '', luogo: '', note: '' })
    setSheetOpen(true)
  }

  function openEvent(ev: CrmEvent, e: React.MouseEvent) {
    e.stopPropagation()
    setSelectedEvent(ev)
    setSheetOpen(true)
  }

  async function handleComplete(id: number) {
    try {
      const updated = await crmApi.updateEvent(id, { stato: 'completato' } as Partial<CrmEvent>)
      setEvents(prev => prev.map(ev => ev.id === id ? updated : ev))
      setSelectedEvent(updated)
      toast.success('Evento completato')
    } catch {
      toast.error('Errore')
    }
  }

  async function handleCancel(id: number) {
    try {
      await crmApi.deleteEvent(id)
      setEvents(prev => prev.map(ev => ev.id === id ? { ...ev, stato: 'annullato' } : ev))
      setSheetOpen(false)
      toast.success('Evento annullato')
    } catch {
      toast.error('Errore')
    }
  }

  async function handleCreate() {
    if (!newForm.data_ora) { toast.error('Inserisci data e ora'); return }
    try {
      const ev = await crmApi.createEvent({
        tipo: newForm.tipo,
        data_ora: newForm.data_ora.replace('T', ' '),
        cliente_id: newForm.cliente_id ? Number(newForm.cliente_id) : undefined,
        luogo: newForm.luogo || undefined,
        note: newForm.note || undefined,
      })
      setEvents(prev => [...prev, ev])
      toast.success('Evento creato')
      setSheetOpen(false)
    } catch {
      toast.error('Errore nella creazione')
    }
  }

  const dayEvents = selectedDay ? eventsForDay(selectedDay) : []
  const isToday = (day: number) =>
    day === today.getDate() && month === today.getMonth() + 1 && year === today.getFullYear()

  return (
    <div className="p-6 flex flex-col gap-4 h-full overflow-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Calendar size={20} className="text-[#e94560]" />
        <h1 className="text-lg font-semibold">CRM — Calendario</h1>
        <div className="flex items-center gap-2 ml-auto">
          <Button variant="ghost" size="icon" onClick={prevMonth}>
            <ChevronLeft size={16} />
          </Button>
          <span className="text-sm font-medium w-40 text-center">
            {MONTHS[month - 1]} {year}
          </span>
          <Button variant="ghost" size="icon" onClick={nextMonth}>
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 gap-1">
        {DAYS.map(d => (
          <div key={d} className="text-center text-xs text-gray-500 py-1 font-medium">
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {cells.map((day, idx) => {
          const dayEvs = day ? eventsForDay(day) : []
          return (
            <div
              key={idx}
              onClick={() => day && openDay(day)}
              className={[
                'min-h-[80px] rounded-md p-1.5 border transition-colors',
                day
                  ? 'cursor-pointer border-transparent hover:border-[#0f3460] hover:bg-[#0f3460]/20'
                  : 'border-transparent pointer-events-none',
                day && isToday(day)
                  ? 'border-[#e94560]/50 bg-[#e94560]/5'
                  : '',
              ].join(' ')}
            >
              {day && (
                <>
                  <div className={`text-xs font-medium mb-1 ${isToday(day) ? 'text-[#e94560]' : 'text-gray-400'}`}>
                    {day}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    {dayEvs.slice(0, 3).map(ev => (
                      <div
                        key={ev.id}
                        onClick={e => openEvent(ev, e)}
                        className={`text-[10px] px-1 py-0.5 rounded truncate cursor-pointer ${eventColor(ev)}`}
                      >
                        {ev.data_ora.slice(11, 16)} {ev.tipo}
                      </div>
                    ))}
                    {dayEvs.length > 3 && (
                      <div className="text-[10px] text-gray-500 px-1">+{dayEvs.length - 3} altri</div>
                    )}
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>

      {/* Sheet — day view or event detail */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className="w-80 overflow-y-auto bg-[#16213e] border-[#0f3460]">
          {selectedEvent ? (
            <>
              <SheetHeader>
                <SheetTitle className="capitalize text-sm">
                  {selectedEvent.tipo} — {selectedEvent.cliente_nome ?? '—'}
                </SheetTitle>
              </SheetHeader>
              <div className="p-4 flex flex-col gap-3 text-sm">
                <div>
                  <span className="text-gray-400 text-xs">Data </span>
                  {new Date(selectedEvent.data_ora).toLocaleString('it-IT')}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 text-xs">Stato </span>
                  <Badge className={`text-[10px] ${eventColor(selectedEvent)}`}>
                    {selectedEvent.stato}
                  </Badge>
                </div>
                {selectedEvent.durata_minuti != null && (
                  <div>
                    <span className="text-gray-400 text-xs">Durata </span>
                    {selectedEvent.durata_minuti} min
                  </div>
                )}
                {selectedEvent.luogo && (
                  <div className="flex items-start gap-1.5">
                    <MapPin size={13} className="mt-0.5 text-gray-400 shrink-0" />
                    <a
                      href={`https://maps.google.com/?q=${encodeURIComponent(selectedEvent.luogo)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline break-words"
                    >
                      {selectedEvent.luogo}
                    </a>
                  </div>
                )}
                {selectedEvent.esito && (
                  <div>
                    <span className="text-gray-400 text-xs">Esito </span>
                    {selectedEvent.esito}
                  </div>
                )}
                {selectedEvent.note && (
                  <div>
                    <span className="text-gray-400 text-xs">Note </span>
                    <p className="mt-0.5 text-gray-300 text-xs whitespace-pre-wrap">{selectedEvent.note}</p>
                  </div>
                )}
                {selectedEvent.stato === 'pianificato' && (
                  <div className="flex gap-2 mt-2 pt-2 border-t border-[#0f3460]">
                    <Button
                      size="sm"
                      className="bg-green-700 hover:bg-green-600 text-xs"
                      onClick={() => handleComplete(selectedEvent.id)}
                    >
                      Completa
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-400 text-xs"
                      onClick={() => handleCancel(selectedEvent.id)}
                    >
                      Annulla
                    </Button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <SheetHeader>
                <SheetTitle className="text-sm">
                  {selectedDay} {MONTHS[(month - 1)]} {year}
                </SheetTitle>
              </SheetHeader>
              <div className="p-4 flex flex-col gap-4">
                {dayEvents.length === 0 ? (
                  <p className="text-xs text-gray-400">Nessun evento per questo giorno.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {dayEvents.map(ev => (
                      <div
                        key={ev.id}
                        onClick={e => openEvent(ev, e)}
                        className="p-2 rounded-md bg-[#0f3460]/40 cursor-pointer hover:bg-[#0f3460]/70 flex items-start gap-2"
                      >
                        <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${dotColor(ev)}`} />
                        <div>
                          <div className="text-xs font-medium capitalize">
                            {ev.tipo} — {ev.cliente_nome ?? '—'}
                          </div>
                          <div className="text-[11px] text-gray-400">
                            {ev.data_ora.slice(11, 16)}{ev.luogo ? ` · ${ev.luogo}` : ''}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="border-t border-[#0f3460] pt-3 flex flex-col gap-2">
                  <p className="text-[11px] text-gray-400 font-medium">Nuovo evento</p>
                  <select
                    value={newForm.tipo}
                    onChange={e => setNewForm(f => ({ ...f, tipo: e.target.value }))}
                    className="bg-[#0f3460]/40 border border-[#0f3460] rounded px-2 py-1.5 text-xs text-gray-200 w-full"
                  >
                    <option value="visita">Visita</option>
                    <option value="chiamata">Chiamata</option>
                    <option value="email">Email</option>
                  </select>
                  <select
                    value={newForm.cliente_id}
                    onChange={e => setNewForm(f => ({ ...f, cliente_id: e.target.value }))}
                    className="bg-[#0f3460]/40 border border-[#0f3460] rounded px-2 py-1.5 text-xs text-gray-200 w-full"
                  >
                    <option value="">Cliente (opzionale)</option>
                    {clienti.map(c => (
                      <option key={c.id} value={c.id}>{c.ragione_sociale}</option>
                    ))}
                  </select>
                  <Input
                    type="datetime-local"
                    value={newForm.data_ora}
                    onChange={e => setNewForm(f => ({ ...f, data_ora: e.target.value }))}
                    className="bg-[#0f3460]/40 border-[#0f3460] text-xs h-8"
                  />
                  <Input
                    placeholder="Luogo (opzionale)"
                    value={newForm.luogo}
                    onChange={e => setNewForm(f => ({ ...f, luogo: e.target.value }))}
                    className="bg-[#0f3460]/40 border-[#0f3460] text-xs h-8"
                  />
                  <Input
                    placeholder="Note (opzionale)"
                    value={newForm.note}
                    onChange={e => setNewForm(f => ({ ...f, note: e.target.value }))}
                    className="bg-[#0f3460]/40 border-[#0f3460] text-xs h-8"
                  />
                  <Button onClick={handleCreate} size="sm" className="text-xs">
                    Crea evento
                  </Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}
