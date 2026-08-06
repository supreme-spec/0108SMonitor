import { ArrowRight } from 'lucide-react'
import { PHOTO_BASE } from '../api/client'

interface Props {
  event: any // Event + person + camera + lastCategoryChange
  liveFrameUrl?: string | null
}

const BADGE: Record<string, string> = {
  BLACKLIST: 'bg-red-500/15 text-red-400',
  NOT_TODAY: 'bg-orange-500/15 text-orange-400',
  SUITE: 'bg-pink-500/15 text-pink-400',
  VIP: 'bg-purple-500/15 text-purple-400',
  CLIENT: 'bg-slate-500/15 text-slate-300',
  STAFF: 'bg-green-500/15 text-green-400',
}

function Badge({ code }: { code?: string | null }) {
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${BADGE[code ?? ''] ?? 'bg-slate-500/15 text-slate-300'}`}>
      {code ?? '—'}
    </span>
  )
}

export default function RecognizedRow({ event, liveFrameUrl }: Props) {
  const person = event.person
  const then = event.categoryCode || event.person_category
  const now = person?.category
  const changed = then && now && then !== now
  const lc = event.lastCategoryChange

  const pulse =
    event.alerted && !event.alertAcked
      ? then === 'BLACKLIST' ? 'alert-pulse-critical' : 'alert-pulse-warning'
      : ''

  const personPhoto = person?.photos?.[0]?.photo_path || person?.photo_path

  return (
    <div className={`rounded-lg border border-kraken-border bg-kraken-panel p-2 ${pulse}`}>
      <div className="flex gap-2">
        {/* LEFT: now (live frame or registered photo) */}
        <img
          src={liveFrameUrl ?? (personPhoto ? `${PHOTO_BASE}/${personPhoto}` : null)}
          alt="Сейчас"
          className="h-16 w-16 rounded-md object-cover flex-shrink-0"
        />
        {/* RIGHT: snapshot at recognition moment */}
        <img
          src={event.snapshot_path ? `${PHOTO_BASE}/${event.snapshot_path}` : null}
          alt="Момент распознавания"
          className="h-16 w-16 rounded-md object-cover flex-shrink-0"
        />

        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-2">
            <span className="truncate text-sm font-bold text-kraken-text">{person?.name ?? event.person_name}</span>
            {event.confidence != null && (
              <span className="text-[10px] text-kraken-muted">
                {Math.round(((Math.max(0.28, Math.min(0.85, event.confidence)) - 0.28) / (0.85 - 0.28)) * 100)}%
              </span>
            )}
          </div>

          {/* Category trajectory */}
          <div className="mt-1 flex flex-wrap items-center gap-1">
            <Badge code={then} />
            {changed && (
              <>
                <ArrowRight size={12} className="text-kraken-muted" />
                <Badge code={now} />
              </>
            )}
            {!changed && <span className="text-[10px] text-kraken-muted">без изменений</span>}
          </div>

          {changed && lc && (
            <p className="mt-0.5 truncate text-[10px] text-kraken-muted">
              {lc.reason} · {new Date(lc.created_at).toLocaleString('ru-RU')}
            </p>
          )}

          <p className="mt-0.5 text-[10px] text-kraken-muted">
            {event.camera?.name ?? `Зона ${event.camera?.zone ?? '?'}`} ·{' '}
            {new Date(event.created_at).toLocaleTimeString('ru-RU')}
          </p>
        </div>
      </div>
    </div>
  )
}
