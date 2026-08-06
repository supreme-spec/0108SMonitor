import { useState } from 'react'
import { ChevronDown, Camera as CameraIcon } from 'lucide-react'
import type { Camera } from '../types'
import AlertBell from './AlertBell'
import rusImg from '../assets/images/imperial_flag_full_bleed_1783510617289.jpg'
import logoImg from '../assets/images/einfach_logo_1783510147919.jpg'

interface TopBarProps {
  cameras: Camera[]
  selectedCameraId: number | null
  onSelectCamera: (id: number) => void
  alertCount: number
  onOpenAlerts: () => void
  releaseButton?: React.ReactNode
  onAvatarChange?: (file: File) => void
  onNavToБД?: () => void
}

export default function TopBar({
  cameras,
  selectedCameraId,
  onSelectCamera,
  alertCount,
  onOpenAlerts,
  releaseButton,
  onAvatarChange,
  onNavToБД,
}: TopBarProps) {
  const selected = cameras.find(c => c.id === selectedCameraId)
  const isOnline = selected?.status === 'online'
  const [avatarSrc, setAvatarSrc] = useState<string>(rusImg)
  const [logoError, setLogoError] = useState(false)
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
    <div className="h-16 w-full relative flex items-center bg-kraken-panel px-4 border-b border-kraken-border flex-shrink-0">

      {/* Block #1: Logo + KRAKEN branding */}
      <div className="flex items-center gap-3 flex-shrink-0">
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

      {/* Active "БД" button (replacing back button) */}
      <button
        onClick={onNavToБД}
        className="ml-4 px-3 py-1.5 rounded-lg bg-kraken-purple/15 text-kraken-purple border border-kraken-purple text-xs font-semibold hover:bg-kraken-purple/30 transition-colors"
      >
        БД
      </button>

      {/* Left: camera selector + quick switcher + live */}
      <div className="flex items-center gap-3 flex-1">
        {/* Camera dropdown */}
        <div className="relative">
          <select
            value={selectedCameraId ?? ''}
            onChange={e => onSelectCamera(Number(e.target.value))}
            className="appearance-none bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-1.5 pr-8 rounded-lg focus:outline-none focus:border-kraken-purple cursor-pointer min-w-[140px]"
          >
            {cameras.length === 0 && <option value="">Нет камер</option>}
            {cameras.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <ChevronDown size={13} className="absolute right-2 top-1/2 -translate-y-1/2 text-kraken-muted pointer-events-none" />
        </div>

        {/* Quick camera switcher buttons */}
        {cameras.length > 0 && (
          <div className="flex items-center gap-1 ml-1">
            {cameras.slice(0, 3).map(camera => (
              <button
                key={camera.id}
                onClick={() => onSelectCamera(camera.id)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  selectedCameraId === camera.id
                    ? 'bg-kraken-purple text-white'
                    : 'bg-kraken-hover text-kraken-muted hover:text-kraken-text hover:bg-kraken-border'
                }`}
                title={camera.name}
              >
                {camera.name.length > 8 ? camera.name.substring(0, 6) + '...' : camera.name}
              </button>
            ))}
            {cameras.length > 3 && (
              <span className="text-kraken-disabled text-xs px-1">+{cameras.length - 3}</span>
            )}
          </div>
        )}

        {/* Live badge */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
          isOnline
            ? 'bg-kraken-green/15 text-kraken-green'
            : 'bg-kraken-hover text-kraken-disabled'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-kraken-green animate-pulse' : 'bg-kraken-disabled'}`} />
          {isOnline ? 'LIVE' : 'ОФЛАЙН'}
        </div>
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
        <AlertBell />

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
