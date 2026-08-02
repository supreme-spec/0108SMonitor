import { useState, useRef, useEffect } from 'react'
import { Video, Users, BookImage, Activity, Camera, Settings, Monitor, Grid2X2, BookOpen, Tag, UserCheck, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import logoImg from '../assets/images/einfach_logo_1783510147919.jpg'

interface SidebarProps {
  currentPage: string
  onNavigate: (page: string) => void
  onProjection?: () => void
  projectionActive?: boolean
}

const NAV_SECTIONS = [
  { title: 'Мониторинг', items: [
    { id: 'live', label: 'Live монитор', icon: Video },
    { id: 'multicam', label: 'Все камеры', icon: Grid2X2 },
  ]},
  { title: 'База данных', items: [
    { id: 'people', label: 'Люди', icon: Users },
    { id: 'chronicle', label: 'Фотохроника', icon: BookImage },
    { id: 'recordings', label: 'Умная съёмка', icon: Video },
    { id: 'events', label: 'События', icon: Activity },
    { id: 'confirmations', label: 'Подтверждения', icon: UserCheck },
    { id: 'categories', label: 'Категории', icon: Tag },
  ]},
  { title: 'Настройки', items: [
    { id: 'cameras', label: 'Камеры', icon: Camera },
    { id: 'requirements', label: 'Требования', icon: BookOpen },
    { id: 'requirements_v2', label: 'Требования (V2)', icon: BookOpen },
    { id: 'settings', label: 'Система', icon: Settings },
  ]},
]

export default function Sidebar({ currentPage, onNavigate, onProjection, projectionActive }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [hovered, setHovered] = useState(false)
  const [logoError, setLogoError] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleMouseEnter = () => {
    if (collapsed) {
      hoverTimerRef.current = setTimeout(() => setHovered(true), 80)
    }
  }

  const handleMouseLeave = () => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    setHovered(false)
  }

  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    }
  }, [])

  return (
    <>
      {/* Кнопка-триггер для collapsed режима */}
      {collapsed && (
        <div
          className="fixed top-4 left-4 z-50"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <button
            onClick={() => { setCollapsed(false); setHovered(false) }}
            className="w-10 h-10 flex items-center justify-center rounded-lg bg-kraken-panel border border-kraken-border text-kraken-muted hover:text-kraken-text hover:border-kraken-accent transition-colors"
          >
            <PanelLeftOpen size={18} />
          </button>

          {/* Всплывающее меню при collapsed */}
          {hovered && (
            <div
              className="absolute left-12 top-0 w-64 bg-kraken-panel border border-kraken-border rounded-xl shadow-2xl p-3 animate-fade-in"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              {/* Logo */}
              <div className="px-3 py-3 flex items-center gap-3 border-b border-kraken-border mb-2">
                <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center flex-shrink-0 overflow-hidden shadow-glow-purple text-lg">
                  {logoError ? (
                    '🐙'
                  ) : (
                    <img
                      src={logoImg}
                      alt="Einfach Jugend"
                      className="w-full h-full object-cover rounded-full"
                      referrerPolicy="no-referrer"
                      onError={() => setLogoError(true)}
                    />
                  )}
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="text-kraken-text font-bold text-sm leading-none tracking-wider uppercase">
                    <span className="text-kraken-purple font-black">KRAKEN</span>
                  </div>
                  <div className="text-kraken-disabled text-[9px] tracking-wider uppercase mt-1">Security Engine</div>
                </div>
              </div>

              {/* Navigation */}
              <nav className="flex flex-col gap-0.5 max-h-[70vh] overflow-y-auto">
                {NAV_SECTIONS.map(section => (
                  <div key={section.title}>
                    <div className="text-kraken-disabled text-[10px] uppercase tracking-widest px-3 pt-2 pb-1.5">
                      {section.title}
                    </div>
                    {section.items.map(item => (
                      <button
                        key={item.id}
                        onClick={() => { onNavigate(item.id); setHovered(false) }}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                          currentPage === item.id
                            ? 'bg-kraken-purple/15 text-kraken-text border-l-2 border-kraken-purple pl-[10px]'
                            : 'text-kraken-muted hover:text-kraken-text hover:bg-kraken-hover'
                        }`}
                      >
                        <item.icon size={16} className={currentPage === item.id ? 'text-kraken-purple' : ''} />
                        <span className="text-sm">{item.label}</span>
                      </button>
                    ))}
                  </div>
                ))}
              </nav>

              {/* Projection button */}
              <div className="mt-3 pt-2 border-t border-kraken-border">
                <button
                  onClick={() => { onProjection?.(); setHovered(false) }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg border transition-colors ${
                    projectionActive
                      ? 'bg-kraken-purple/30 border-kraken-purple text-kraken-purple'
                      : 'bg-kraken-purple/20 border-kraken-purple/40 text-kraken-purple hover:bg-kraken-purple/30'
                  }`}
                >
                  <Monitor size={15} />
                  <span className="text-xs font-semibold tracking-wide uppercase">Передать на экран</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Основной sidebar */}
      <div
        ref={sidebarRef}
        className={`h-screen bg-kraken-base flex flex-col border-r border-kraken-border flex-shrink-0 transition-all duration-300 ${
          collapsed ? 'w-16' : 'w-56'
        }`}
        onMouseEnter={collapsed ? handleMouseEnter : undefined}
        onMouseLeave={collapsed ? handleMouseLeave : undefined}
      >
        {!collapsed && (
          <>
            {/* Logo */}
            <div className="px-4 py-4 flex items-center gap-3 border-b border-kraken-border">
              <div className="w-12 h-12 rounded-full bg-black flex items-center justify-center flex-shrink-0 overflow-hidden shadow-glow-purple text-xl">
                {logoError ? (
                  '🐙'
                ) : (
                  <img
                    src={logoImg}
                    alt="Einfach Jugend"
                    className="w-full h-full object-cover rounded-full"
                    referrerPolicy="no-referrer"
                    onError={() => setLogoError(true)}
                  />
                )}
              </div>
              <div className="flex flex-col min-w-0">
                <div className="text-kraken-text font-bold text-base leading-none tracking-wider uppercase flex items-center gap-1.5">
                  <span className="text-kraken-purple font-black">KRAKEN</span>
                </div>
                <div className="text-kraken-disabled text-[9px] tracking-wider uppercase mt-1">Security Engine</div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-3 flex flex-col gap-0.5 overflow-y-auto">
              {NAV_SECTIONS.map(section => (
                <div key={section.title}>
                  <div className="text-kraken-disabled text-[10px] uppercase tracking-widest px-3 pt-2 pb-1.5">
                    {section.title}
                  </div>
                  {section.items.map(item => (
                    <NavItem
                      key={item.id}
                      id={item.id}
                      label={item.label}
                      icon={item.icon}
                      current={currentPage}
                      onNavigate={onNavigate}
                    />
                  ))}
                </div>
              ))}
            </nav>

            {/* Projection + collapse */}
            <div className="p-3 border-t border-kraken-border flex flex-col gap-2">
              <button
                onClick={onProjection}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg border transition-colors ${
                  projectionActive
                    ? 'bg-kraken-purple/30 border-kraken-purple text-kraken-purple'
                    : 'bg-kraken-purple/20 border-kraken-purple/40 text-kraken-purple hover:bg-kraken-purple/30'
                }`}
              >
                <Monitor size={15} />
                <span className="text-xs font-semibold tracking-wide uppercase">Передать на экран</span>
              </button>
              <button
                onClick={() => setCollapsed(true)}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg border border-kraken-border text-kraken-muted hover:text-kraken-text hover:border-kraken-accent transition-colors"
              >
                <PanelLeftClose size={15} />
                <span className="text-xs font-semibold tracking-wide uppercase">Свернуть</span>
              </button>
            </div>
          </>
        )}

        {collapsed && (
          <div className="flex flex-col items-center pt-4 gap-2">
            {NAV_SECTIONS.flatMap(s => s.items).map(item => (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                title={item.label}
                className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
                  currentPage === item.id
                    ? 'bg-kraken-purple/20 text-kraken-purple'
                    : 'text-kraken-muted hover:text-kraken-text hover:bg-kraken-hover'
                }`}
              >
                <item.icon size={18} />
              </button>
            ))}
            <div className="mt-auto mb-4 flex flex-col gap-2">
              <button
                onClick={onProjection}
                title="Передать на экран"
                className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
                  projectionActive
                    ? 'bg-kraken-purple/20 text-kraken-purple'
                    : 'text-kraken-muted hover:text-kraken-text hover:bg-kraken-hover'
                }`}
              >
                <Monitor size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function NavItem({ id, label, icon: Icon, current, onNavigate }: {
  id: string; label: string; icon: React.ElementType; current: string; onNavigate: (p: string) => void
}) {
  const active = current === id
  return (
    <button
      onClick={() => onNavigate(id)}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
        active
          ? 'bg-kraken-purple/15 text-kraken-text border-l-2 border-kraken-purple pl-[10px]'
          : 'text-kraken-muted hover:text-kraken-text hover:bg-kraken-hover'
      }`}
    >
      <Icon size={16} className={active ? 'text-kraken-purple' : ''} />
      <span className="text-sm">{label}</span>
    </button>
  )
}
