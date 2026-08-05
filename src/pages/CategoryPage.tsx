import { ArrowLeft } from 'lucide-react'
import People from './People'

interface CategoryPageProps {
  categoryId: string
  title: string
}

// Map category IDs to their actual category codes in the database
const categoryCodeMap: Record<string, string> = {
  'stops': 'BLACKLIST',
  'not_today': 'RESPONSE', // Using RESPONSE as closest equivalent for "not today"
  'guests': 'CLIENT',
  'suite': 'VIP',
  'staff': 'STAFF',
  'vip': 'VIP'
}

export default function CategoryPage({ categoryId, title }: CategoryPageProps) {
  const categoryCode = categoryCodeMap[categoryId] || categoryId.toUpperCase()

  return (
    <div className="flex flex-col h-full bg-kraken-base">
      {/* Header */}
      <div className="flex items-center gap-4 p-4 border-b border-kraken-border bg-kraken-panel">
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'hero' }))}
          className="p-2 rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-text transition-colors"
          title="Назад к базе данных"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-kraken-text font-bold text-lg">{title}</h1>
          <p className="text-kraken-muted text-xs">Категория базы данных</p>
        </div>
      </div>

      {/* Content - People component with category filter */}
      <div className="flex-1 overflow-hidden">
        <People initialCategory={categoryCode} />
      </div>
    </div>
  )
}
