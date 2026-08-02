import { useState } from 'react'
import { Bell, ChevronDown, ChevronLeft, Camera as CameraIcon } from 'lucide-react'
import type { Camera } from '../types'
import rusImg from '../assets/images/imperial_flag_full_bleed_1783510617289.jpg'

interface TopBarProps {
  cameras: Camera[]
  selectedCameraId: number | null
  onSelectCamera: (id: number) => void
  alertCount: number
  onOpenAlerts: () => void
  releaseButton?: React.ReactNode
  onAvatarChange?: (file: File) => void
}

export default function TopBar({
  cameras,
  selectedCameraId,
  onSelectCamera,
  alertCount,
  onOpenAlerts,
  releaseButton,
  onAvatarChange,
}: TopBarProps) {
  const selected = cameras.find(c => c.id === selectedCameraId)
  const isOnline = selected?.status === 'online'
  const [avatarSrc, setAvatarSrc] = useState<string>(rusImg)
  const [showHint, setShowHint] = useState(false)

  const handleAvatarFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    setAvatarSrc(url)
    onAvatarChange?.(file)
    // сбрасываем value чтобы можно было выбрать тот же файл повторно
    e.target.value = ''
  }

  return (
    <div className="h-16 relative flex items-center bg-kraken-panel px-4 border-b border-kraken-border flex-shrink-0">

      {/* Left: back + release button */}
      <div className="flex items-center gap-3 flex-1">
        <button className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-text transition-colors">
          <ChevronLeft size={20} />
        </button>
      </div>

      {/* Right: release button + bell + user */}
      <div className="flex items-center gap-2">
        {releaseButton && (
          <>
            {releaseButton}
            <div className="w-px h-6 bg-kraken-border mx-1" />
          </>
        )}

        {/* Alerts bell */}
        <button
          onClick={onOpenAlerts}
          className="relative w-10 h-10 flex items-center justify-center rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-text transition-colors"
        >
          <Bell size={16} />
          {alertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-kraken-red rounded-full text-white text-[10px] flex items-center justify-center font-bold px-0.5">
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </button>

        <div className="w-px h-6 bg-kraken-border mx-1" />

        {/* User — label обёртывает input, нет JS .click() → не вешает UI */}
        <label
          className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-kraken-hover transition-colors cursor-pointer"
          onMouseEnter={() => setShowHint(true)}
          onMouseLeave={() => setShowHint(false)}
          title="Нажмите чтобы сменить фото"
        >
          <div className="relative w-10 h-10 rounded-full overflow-hidden flex-shrink-0 border-2 border-kraken-purple shadow-glow-purple">
            <img src={avatarSrc} alt="Охрана" className="w-full h-full object-cover" />
            <div className={`absolute inset-0 bg-black/50 flex items-center justify-center transition-opacity ${showHint ? 'opacity-100' : 'opacity-0'}`}>
              <CameraIcon size={14} className="text-white" />
            </div>
          </div>
          <div className="flex flex-col leading-none">
            <span className="text-kraken-text text-xs font-semibold">Охрана</span>
            <span className="text-kraken-disabled text-[10px]">Security</span>
          </div>
          {/* input внутри label — браузер сам открывает диалог без блокировки */}
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleAvatarFile}
          />
        </label>
      </div>
    </div>
  )
}
