import { useState } from 'react'
import RequirementsHub from './RequirementsHub'
import Description from './pages/Description'
import TechStack from './pages/TechStack'
import Server from './pages/Server'
import Cameras from './pages/Cameras'
import Lighting from './pages/Lighting'
import Photos from './pages/Photos'
import Thresholds from './pages/Thresholds'
import Performance from './pages/Performance'
import KnowThis from './pages/KnowThis'
import type { ReactNode } from 'react'

const pages: Record<string, ReactNode> = {
  description: <Description />,
  techstack: <TechStack />,
  server: <Server />,
  cameras: <Cameras />,
  lighting: <Lighting />,
  photos: <Photos />,
  thresholds: <Thresholds />,
  performance: <Performance />,
  knowthis: <KnowThis />,
}

export default function RequirementsV2() {
  const [current, setCurrent] = useState<string | null>(null)

  if (!current) return <RequirementsHub onSelect={(id: string) => setCurrent(id)} />

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto pb-8 p-4">
        <button
          onClick={() => setCurrent(null)}
          className="mb-4 flex items-center gap-2 text-kraken-muted hover:text-kraken-text transition-colors"
        >
          <span className="text-kraken-purple">←</span>
          <span className="text-sm">Назад к разделам</span>
        </button>
        {pages[current]}
      </div>
    </div>
  )
}
