import {
  BookOpen,
  Cpu,
  HardDrive,
  Camera,
  Sun,
  Image,
  Zap,
  Target,
  Monitor,
} from 'lucide-react'

const gridItems = [
  { id: 'description',   label: 'Описание системы',     icon: BookOpen,  color: 'text-kraken-blue',    emoji: '📘' },
  { id: 'techstack',    label: 'Технологический стек', icon: Zap,       color: 'text-kraken-purple',  emoji: '⚡' },
  { id: 'server',       label: 'Требования к ПК',      icon: Cpu,       color: 'text-kraken-blue',    emoji: '🖥' },
  { id: 'cameras',      label: 'Видеокамеры',          icon: Camera,    color: 'text-kraken-green',   emoji: '📷' },
  { id: 'lighting',     label: 'Освещение',            icon: Sun,       color: 'text-yellow-400',     emoji: '💡' },
  { id: 'photos',       label: 'Фотографии',           icon: Image,     color: 'text-kraken-purple',  emoji: '🖼' },
  { id: 'thresholds',   label: 'Пороги распознавания', icon: Target,    color: 'text-kraken-blue',    emoji: '🎯' },
  { id: 'performance',  label: 'Производительность',  icon: HardDrive, color: 'text-kraken-green',   emoji: '📈' },
  { id: 'knowthis',     label: 'Что нужно знать',      icon: Monitor,   color: 'text-kraken-purple',  emoji: '❗' },
]

interface HubProps {
  onSelect: (id: string) => void
}

export default function RequirementsHub({ onSelect }: HubProps) {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto flex flex-col gap-6 pb-8 p-4">

        {/* ── Header ── */}
        <div className="flex items-center gap-3">
          <h1 className="text-kraken-text text-xl font-bold">Системные требования</h1>
          <span className="text-xs text-kraken-disabled bg-kraken-hover px-2 py-0.5 rounded-full">
            Kraken Security System
          </span>
        </div>

        {/* ── Grid of buttons ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {gridItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              className="bg-kraken-panel border border-kraken-border rounded-xl p-5 text-left transition-all duration-200 hover:border-kraken-purple/60 hover:shadow-[0_0_20px_rgba(168,85,247,0.15)] flex flex-col h-full"
            >
              <div className="flex items-start gap-4">
                <span className="text-3xl">{item.emoji}</span>
                <div className="flex-1 min-w-0">
                  <h2 className={`text-lg font-semibold ${item.color} mb-1 break-words leading-tight`}>
                    {item.label}
                  </h2>
                </div>
                <item.icon size={20} className={`${item.color} flex-shrink-0 self-start mt-0.5`} />
              </div>
            </button>
          ))}
        </div>

        {/* ── Note ── */}
        <div className="mt-2 text-xs text-kraken-disabled text-center">
          Нажмите любую кнопку — сразу переход к полному разделу без прокрутки
        </div>

      </div>
    </div>
  )
}
