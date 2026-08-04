import { Video, Users, BookImage, Activity, Camera, Settings, Monitor, Grid2X2, BookOpen, Tag, UserCheck } from 'lucide-react'

interface SidebarProps {
  currentPage: string
  onNavigate: (page: string) => void
  onProjection?: () => void
  projectionActive?: boolean
}

export default function Sidebar({ currentPage, onNavigate, onProjection, projectionActive }: SidebarProps) {
  return (
    <div className="w-16 h-full bg-kraken-base flex flex-col border-r border-kraken-border flex-shrink-0">
      <nav className="flex-1 py-3 flex flex-col gap-0.5 overflow-y-auto">
        <NavItem id="live"       label="Live монитор"  icon={Video}     current={currentPage} onNavigate={onNavigate} />
        <NavItem id="multicam"  label="Все камеры"    icon={Grid2X2}   current={currentPage} onNavigate={onNavigate} />
        <NavItem id="people"     label="Люди"         icon={Users}      current={currentPage} onNavigate={onNavigate} />
        <NavItem id="chronicle"  label="Фотохроника"  icon={BookImage}  current={currentPage} onNavigate={onNavigate} />
        <NavItem id="recordings" label="Умная съёмка"  icon={Video}      current={currentPage} onNavigate={onNavigate} />
        <NavItem id="events"     label="События"      icon={Activity}   current={currentPage} onNavigate={onNavigate} />
        <NavItem id="confirmations" label="Подтверждения" icon={UserCheck} current={currentPage} onNavigate={onNavigate} />
        <NavItem id="categories" label="Категории"    icon={Tag}        current={currentPage} onNavigate={onNavigate} />
        <NavItem id="cameras"       label="Камеры"        icon={Camera}    current={currentPage} onNavigate={onNavigate} />
        <NavItem id="requirements"  label="Требования"    icon={BookOpen}  current={currentPage} onNavigate={onNavigate} />
        <NavItem id="requirements_v2" label="Требования (V2)" icon={BookOpen} current={currentPage} onNavigate={onNavigate} />
        <NavItem id="settings"      label="Система"       icon={Settings}  current={currentPage} onNavigate={onNavigate} />
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
      className={`w-full flex items-center justify-center py-3 rounded-lg transition-colors ${
        active
          ? 'bg-kraken-purple/15 text-kraken-purple'
          : 'text-kraken-muted hover:text-kraken-text hover:bg-kraken-hover'
      }`}
      title={label}
    >
      <Icon size={20} className={active ? 'text-kraken-purple' : ''} />
    </button>
  )
}
