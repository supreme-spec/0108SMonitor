import { useState } from 'react'
import type { KrakenEvent } from '../types'
import CategoryBadge from './CategoryBadge'
import { PHOTO_BASE } from '../api/client'
import RecognizedRow from './RecognizedRow'

interface Props {
  events: KrakenEvent[]
  maxItems?: number
  liveFrameUrl?: string | null
}

export default function EventsFeed({ events, maxItems = 50, liveFrameUrl }: Props) {
  const items = events.slice(0, maxItems)

  if (items.length === 0) {
    return (
      <div className="text-kraken-disabled text-sm text-center py-8">
        Событий пока нет
      </div>
    )
  }

  return (
    <div className="flex flex-col divide-y divide-kraken-border">
      {items.map(ev => (
        <RecognizedRow key={ev.id} event={ev} liveFrameUrl={liveFrameUrl} />
      ))}
    </div>
  )
}
