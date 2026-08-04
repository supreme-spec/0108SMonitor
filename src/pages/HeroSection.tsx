import { useState } from 'react'
import { X, CalendarX, Users, UserCheck, Shield, Star } from 'lucide-react'

const dbButtons = [
  {
    id: 'stops',
    label: 'СТОПЫ',
    icon: X,
    description: 'Чёрный список',
    color: 'from-red-500 to-pink-500'
  },
  {
    id: 'not_today',
    label: 'НЕ СЕГОДНЯ',
    icon: CalendarX,
    description: 'Отложенные визиты',
    color: 'from-orange-500 to-red-500'
  },
  {
    id: 'guests',
    label: 'ГОСТИ',
    icon: Users,
    description: 'Гости и клиенты',
    color: 'from-blue-500 to-cyan-500'
  },
  {
    id: 'suite',
    label: 'СВИТА',
    icon: UserCheck,
    description: 'VIP сопровождение',
    color: 'from-purple-500 to-indigo-500'
  },
  {
    id: 'staff',
    label: 'ПЕРСОНАЛ',
    icon: Shield,
    description: 'Сотрудники и охрана',
    color: 'from-green-500 to-emerald-500'
  },
  {
    id: 'vip',
    label: 'VIP',
    icon: Star,
    description: 'VIP персоны',
    color: 'from-yellow-500 to-orange-500'
  },
]

export default function HeroSection() {
  const [activeDBButton, setActiveDBButton] = useState<string | null>(null)

  const handleDBButtonClick = (id: string) => {
    setActiveDBButton(prev => prev === id ? null : id)
  }

  return (
    <div className="flex flex-col h-full bg-kraken-base overflow-auto">
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-black text-kraken-text tracking-wider mb-2">
              БАЗА ДАННЫХ
            </h1>
            <p className="text-kraken-muted text-sm">
              Выберите категорию для просмотра
            </p>
          </div>

          {/* 6 кнопок сеткой 2x3 */}
          <div className="grid grid-cols-2 gap-4">
            {dbButtons.map((btn) => {
              const isActive = activeDBButton === btn.id
              return (
                <button
                  key={btn.id}
                  onClick={() => handleDBButtonClick(btn.id)}
                  className={`relative group p-6 rounded-2xl border-2 transition-all duration-300 ${
                    isActive
                      ? 'border-kraken-purple bg-kraken-purple/10 scale-105'
                      : 'border-kraken-border bg-kraken-panel hover:border-kraken-purple/50 hover:scale-[1.02]'
                  }`}
                >
                  {/* Градиентный фон при наведении */}
                  <div
                    className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${btn.color} opacity-0 group-hover:opacity-10 transition-opacity`}
                  />

                  <div className="relative flex flex-col items-center gap-3">
                    <div className={`p-4 rounded-xl bg-gradient-to-br ${btn.color} shadow-lg`}>
                      <btn.icon size={32} className="text-white" />
                    </div>
                    <div className="text-center">
                      <div className="text-kraken-text font-black text-xl tracking-wider mb-1">
                        {btn.label}
                      </div>
                      <div className="text-kraken-muted text-xs">{btn.description}</div>
                    </div>
                  </div>

                  {/* Индикатор активности */}
                  {isActive && (
                    <div className="absolute top-3 right-3 w-3 h-3 bg-kraken-purple rounded-full animate-pulse" />
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
