import { Video, Users, BookImage, Activity, Camera, Settings, Monitor, Grid2X2, BookOpen, Tag, UserCheck } from 'lucide-react'

interface SidebarProps {
  currentPage: string
  onNavigate: (page: string) => void
  onProjection?: () => void
  projectionActive?: boolean
  activePage?: string
}

export default function Sidebar({ currentPage, onNavigate, onProjection, projectionActive, activePage }: SidebarProps) {
  const effectivePage = activePage || currentPage
  return (
    <div className="w-16 h-full bg-kraken-base flex flex-col border-r border-kraken-border flex-shrink-0">
      <nav className="flex-1 py-3 flex flex-col gap-0.5 overflow-y-auto">
        <NavItem id="live"       label="Live монитор"  icon={Video}     current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="multicam"  label="Все камеры"    icon={Grid2X2}   current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="people"     label="Люди"         icon={Users}      current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="chronicle"  label="Фотохроника"  icon={BookImage}  current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="recordings" label="Умная съёмка"  icon={Video}      current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="events"     label="События"      icon={Activity}   current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="confirmations" label="Подтверждения" icon={UserCheck} current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="categories" label="Категории"    icon={Tag}        current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="cameras"       label="Камеры"        icon={Camera}    current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="requirements"  label="Требования"    icon={BookOpen}  current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="requirements_v2" label="Требования (V2)" icon={BookOpen} current={effectivePage} onNavigate={onNavigate} />
        <NavItem id="settings"      label="Система"       icon={Settings}  current={effectivePage} onNavigate={onNavigate} />
      </nav>

      <div className="p-3 border-t border-kraken-border">
        <button
          onClick={onProjection}
          className={`w-full flex items-center justify-center py-2.5 rounded-lg border transition-colors ${
            projectionActive
              ? 'bg-kraken-purple/30 border-kraken-purple text-kraken-purple'
              : 'bg-kraken-purple/20 border-kraken-purple/40 text-kraken-purple hover:bg-kraken-purple/30'
          }`}
          title="Передать на экран"
        >
          <Monitor size={20} />
        </button>
      </div>
    </div>
  )
}

function NavItem({
  id, label, icon: Icon, current, onNavigate,
}: {
  id: string; label: string; icon: React.ElementType
  current: string; onNavigate: (p: string) => void
}) {
  const active = current === id
  return (
    <button
      onClick={() => onNavigate(id)}
      className={[
        'w-full flex items-center justify-center py-3 rounded-lg transition-all duration-200 relative',
        active
          ? 'bg-kraken-purple/20 text-kraken-purple shadow-[0_0_12px_rgba(124,58,237,0.35)]'
          : 'text-kraken-muted hover:text-kraken-text hover:bg-kraken-hover',
      ].join(' ')}
      title={label}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-7 rounded-r-full bg-kraken-purple shadow-[0_0_8px_rgba(124,58,237,0.6)]" />
      )}
      <Icon size={20} className={active ? 'text-kraken-purple' : ''} />
    </button>
  )
}
