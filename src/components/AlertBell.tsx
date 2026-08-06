import { useEffect, useState } from 'react'
import { Bell, Check } from 'lucide-react'
import { apiFetch } from '../api/client'

interface UnackedAlert {
  id: number
  created_at: string
  categoryCode?: string | null
  person_name?: string | null
  camera?: { name?: string | null; zone?: string | null } | null
}

const LEVEL_COLOR: Record<string, string> = {
  BLACKLIST: 'text-kraken-red',
  NOT_TODAY: 'text-kraken-orange',
  SUITE: 'text-pink-400',
  VIP: 'text-kraken-green',
}

export default function AlertBell() {
  const [items, setItems] = useState<UnackedAlert[]>([])
  const [open, setOpen] = useState(false)

  const load = () =>
    apiFetch<UnackedAlert[]>('/alerts/unacked').then(setItems).catch(() => {})

  useEffect(() => {
    load()
    window.addEventListener('app-alert', load as EventListener)
    window.addEventListener('app-alert-ack', load as EventListener)
    const t = setInterval(load, 15000)
    return () => {
      clearInterval(t)
      window.removeEventListener('app-alert', load as EventListener)
      window.removeEventListener('app-alert-ack', load as EventListener)
    }
  }, [])

  const ack = async (id: number) => {
    await apiFetch(`/alerts/${id}/ack`, { method: 'POST' }).catch(() => {})
    load()
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="relative w-10 h-10 flex items-center justify-center rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-text transition-colors"
        title="Неподтверждённые алерты"
      >
        <Bell size={18} />
        {items.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] rounded-full bg-kraken-red px-1 text-center text-[10px] font-bold text-white">
            {items.length > 9 ? '9+' : items.length}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-kraken-border bg-kraken-panel shadow-2xl">
          <div className="border-b border-kraken-border px-3 py-2 text-xs font-semibold text-kraken-muted">
            НЕПОДТВЕРЖДЁННЫЕ АЛЕРТЫ
          </div>
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 && (
              <p className="px-3 py-4 text-center text-xs text-kraken-muted">Нет алертов</p>
            )}
            {items.map(a => (
              <div key={a.id} className="flex items-center gap-2 border-b border-kraken-border/50 px-3 py-2">
                <div className="flex-1 text-xs">
                  <span className={`font-bold ${LEVEL_COLOR[a.categoryCode ?? ''] ?? 'text-kraken-text'}`}>
                    {a.categoryCode}
                  </span>{' '}
                  <span className="text-kraken-text">{a.person_name}</span>
                  <div className="text-[10px] text-kraken-muted">
                    {a.camera?.name ?? `Зона ${a.camera?.zone ?? '?'}`} ·{' '}
                    {new Date(a.created_at).toLocaleTimeString('ru-RU')}
                  </div>
                </div>
                <button
                  onClick={() => ack(a.id)}
                  className="rounded-md border border-kraken-border p-1.5 text-kraken-muted hover:border-kraken-purple/50 hover:text-kraken-text"
                  title="Принято"
                >
                  <Check size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
