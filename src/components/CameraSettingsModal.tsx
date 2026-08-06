import { useState, useEffect, useMemo } from 'react'
import { X, Wifi, WifiOff, RefreshCw, Play, Square, Video, Settings2, Save, Search, Eye, EyeOff, Copy } from 'lucide-react'
import type { Camera } from '../types'
import { apiFetch } from '../api/client'

/* ================= Типы ================= */

interface StreamRow {
  codec: string
  gop: number
  fps: number
  resolution: string
  bitrate: number
  sourceLabel?: 'onvif' | 'rtsp' | 'probe' | 'template' | 'manual' | 'unknown'
}

interface CameraSettingsModalProps {
  camera: Camera
  onClose: () => void
  onSaved: () => void
}

/* ================= Справочники ================= */

const CODECS = ['H.264', 'H.265']
const RESOLUTION_PRESETS = [
  '3840x2160', '3072x1728', '2688x1520', '2560x1440', '2304x1296',
  '2048x1536', '1920x1080', '1280x960', '1280x720',
  '720x576', '704x576', '640x480', '640x360', '480x360', '352x288', '320x240',
]

/* ================= Примитивы ================= */

const inputCls =
  'w-full bg-kraken-base border border-kraken-border text-kraken-text text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple transition-colors'
const labelCls = 'text-kraken-muted text-[10px] mb-1 block uppercase tracking-wider'
const btnGhost =
  'flex items-center gap-2 text-xs bg-kraken-purple/10 hover:bg-kraken-purple/20 text-kraken-purple px-3 py-2 rounded-lg transition-colors disabled:opacity-50'

function Field({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={className}>
      <span className={labelCls}>{label}</span>
      {children}
    </div>
  )
}

function Section({ title, right, children, className = '' }: { title: string; right?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={'p-4 rounded-xl bg-kraken-hover border border-kraken-border ' + className}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-kraken-text text-sm font-semibold">{title}</h3>
        {right}
      </div>
      {children}
    </section>
  )
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === 'online'
      ? 'text-kraken-green bg-kraken-green/10 border-kraken-green/20'
      : 'text-kraken-disabled bg-kraken-base border-kraken-border'
  return (
    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      {status === 'online' ? 'ОНЛАЙН' : status === 'connecting' ? 'ПОДКЛЮЧЕНИЕ' : 'ОФЛАЙН'}
    </span>
  )
}

function SourceBadge({ source }: { source?: string }) {
  const label =
    source === 'onvif' ? 'ONVIF' :
    source === 'rtsp' ? 'RTSP' :
    source === 'probe' ? 'FFprobe' :
    source === 'template' ? 'Шаблон' :
    source === 'manual' ? 'Ручной' : 'Неизвестно'
  const cls =
    source === 'onvif' ? 'border-kraken-purple/40 text-kraken-purple bg-kraken-purple/10' :
    source === 'rtsp' ? 'border-kraken-blue/40 text-kraken-blue bg-kraken-blue/10' :
    source === 'probe' ? 'border-green-500/40 text-green-400 bg-green-500/10' :
    source === 'template' ? 'border-kraken-orange/40 text-kraken-orange bg-kraken-orange/10' :
    source === 'manual' ? 'border-kraken-border text-kraken-muted bg-kraken-base' :
    'border-kraken-red/40 text-kraken-red bg-kraken-red/10'
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${cls}`}>{label}</span>
  )
}

function RtspLine({ url }: { url?: string }) {
  const [show, setShow] = useState(false)
  const [copied, setCopied] = useState(false)
  const safeUrl = url ?? ''
  const masked = useMemo(() => safeUrl.replace(/(rtsp:\/\/[^:]+:)[^@]+(@)/, '$1••••••$2'), [safeUrl])
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(safeUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch { /* clipboard недоступен */ }
  }
  if (!safeUrl) return <div className="mt-1 text-[11px] text-kraken-muted">Источник не задан</div>
  return (
    <div className="mt-1 flex items-center gap-2">
      <code className="truncate font-mono text-[11px] text-kraken-muted">{show ? safeUrl : masked}</code>
      <button type="button" className="text-[11px] text-kraken-muted hover:text-kraken-text" onClick={() => setShow((s) => !s)}>
        {show ? 'скрыть' : 'показать'}
      </button>
      <button type="button" className="text-[11px] text-kraken-muted hover:text-kraken-text" onClick={copy}>
        {copied ? 'скопировано' : 'копия'}
      </button>
    </div>
  )
}

function ResolutionInput({ id, value, disabled, onChange }: { id: string; value: string; disabled?: boolean; onChange: (v: string) => void }) {
  return (
    <>
      <input
        list={id}
        value={value}
        disabled={disabled}
        placeholder="1920x1080"
        pattern="\d{3,4}x\d{3,4}"
        title="Формат: ШИРИНАxВЫСОТА, например 720x576"
        className={inputCls}
        onChange={(e) => onChange(e.target.value)}
      />
      <datalist id={id}>
        {RESOLUTION_PRESETS.map((r) => <option key={r} value={r} />)}
      </datalist>
    </>
  )
}

/* ================= Карточка потока ================= */

function StreamCard({ title, row, listId, canDisable = true, onChange }: {
  title: string
  row: StreamRow
  listId: string
  canDisable?: boolean
  onChange: (next: StreamRow) => void
}) {
  const set = (p: Partial<StreamRow>) => onChange({ ...row, ...p })
  return (
    <div className="rounded-lg border border-kraken-border bg-kraken-base/60 p-3">
      <div className="mb-2 flex items-center justify-between">
        <label className="flex items-center gap-2 text-xs font-semibold text-kraken-text">
          {canDisable && (
            <input type="checkbox" checked={row.codec !== ''} onChange={(e) => set({ codec: e.target.checked ? 'H.264' : '' })} />
          )}
          {title}
        </label>
        <SourceBadge source={row.sourceLabel} />
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Field label="Кодек">
          <select className={inputCls} value={row.codec} disabled={!row.codec} onChange={(e) => set({ codec: e.target.value })}>
            <option value="">—</option>
            {CODECS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="Разрешение">
          <ResolutionInput id={listId} value={row.resolution} disabled={!row.codec} onChange={(resolution) => set({ resolution })} />
        </Field>
        <Field label="GOP">
          <input type="number" min={1} max={400} className={inputCls} value={row.gop} disabled={!row.codec} onChange={(e) => set({ gop: Number(e.target.value) })} />
        </Field>
        <Field label="Огранич. FPS">
          <input type="number" min={1} max={30} className={inputCls} value={row.fps} disabled={!row.codec} onChange={(e) => set({ fps: Number(e.target.value) })} />
        </Field>
        <Field label="Битрейт, кбит/с">
          <input type="number" min={64} max={16384} step={64} className={inputCls} value={row.bitrate} disabled={!row.codec} onChange={(e) => set({ bitrate: Number(e.target.value) })} />
        </Field>
      </div>
    </div>
  )
}

/* ================= Модалка ================= */

export default function CameraSettingsModal({ camera, onClose, onSaved }: CameraSettingsModalProps) {
  const [renderError, setRenderError] = useState<string | null>(null)

  if (renderError) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <div className="panel p-6 w-full max-w-md mx-4 animate-fade-in" onClick={e => e.stopPropagation()}>
          <h3 className="text-kraken-text font-bold text-lg mb-2">Ошибка рендера</h3>
          <pre className="text-red-400 text-xs whitespace-pre-wrap mb-4">{renderError}</pre>
          <button onClick={onClose} className="w-full btn-primary">Закрыть</button>
        </div>
      </div>
    )
  }

  const [name, setName] = useState(camera.name)
  const [source, setSource] = useState(camera.source)
  const [zone, setZone] = useState(camera.zone ?? '')
  const [smartRec, setSmartRec] = useState(camera.is_smart_recording)
  const [chronicle, setChronicle] = useState(camera.is_chronicle)
  const [ipAddress, setIpAddress] = useState(camera.ip_address ?? '')
  const [ipPort, setIpPort] = useState(camera.ip_port?.toString() ?? '554')
  const [username, setUsername] = useState(camera.username ?? '')
  const [password, setPassword] = useState(camera.password ?? '')
  const [useAnalytics, setUseAnalytics] = useState(camera.use_camera_analytics ?? false)

  const [streamSettings, setStreamSettings] = useState<{ row1: StreamRow; row2: StreamRow } | null>(null)
  const [streamLoading, setStreamLoading] = useState(false)
  const [passportProfiles, setPassportProfiles] = useState<any[]>([])
  const [aiStreamProfileId, setAiStreamProfileId] = useState<string | null>(null)
  const [refreshSteps, setRefreshSteps] = useState<Array<{ label: string; status: 'pending' | 'active' | 'done' | 'error'; detail?: string }>>([])
  const [refreshRunning, setRefreshRunning] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [alertState, setAlertState] = useState<{ isOpen: boolean; title: string; message: string } | null>(null)

  const defaultRow: StreamRow = { codec: 'H.264', gop: 30, fps: camera.fps || 25, resolution: '1920x1080', bitrate: 4096, sourceLabel: 'manual' }

  useEffect(() => {
    loadPassportData()
  }, [camera.id, camera.stream_profiles])

  function loadPassportData() {
    const profiles = parsePassportProfiles(camera)
    setPassportProfiles(profiles)
    setAiStreamProfileId(camera.ai_stream_profile_id || null)
    loadStreamSettings()
  }

  function parsePassportProfiles(cam: Camera): any[] {
    if (!cam?.stream_profiles) return []
    try {
      const parsed = JSON.parse(cam.stream_profiles)
      if (Array.isArray(parsed)) return parsed
      if (parsed && Array.isArray(parsed.profiles)) return parsed.profiles
      return []
    } catch {
      return []
    }
  }

  async function loadStreamSettings() {
    setStreamLoading(true)
    try {
      const data = await apiFetch<{ row1: StreamRow; row2: StreamRow }>(`/cameras/${camera.id}/stream-settings`)
      setStreamSettings(data)
    } catch {
      setStreamSettings({ row1: defaultRow, row2: { ...defaultRow, bitrate: 2048, sourceLabel: 'manual' } })
    } finally {
      setStreamLoading(false)
    }
  }

  async function handleRefreshPassport() {
    if (refreshRunning) return
    setRefreshRunning(true)
    const steps = [
      { label: 'Ping', status: 'pending' as const },
      { label: 'TCP :554', status: 'pending' as const },
      { label: 'ONVIF', status: 'pending' as const },
      { label: 'GetProfiles', status: 'pending' as const },
      { label: 'RTSP probe', status: 'pending' as const },
      { label: 'FFprobe', status: 'pending' as const },
      { label: 'Сравнение', status: 'pending' as const },
      { label: 'Валидация AI stream', status: 'pending' as const },
    ]
    setRefreshSteps(steps)

    try {
      setRefreshSteps(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'active' } : s))
      await new Promise(r => setTimeout(r, 400))

      setRefreshSteps(prev => prev.map((s, i) => i === 0 ? { ...s, status: 'done' } : i === 1 ? { ...s, status: 'active' } : s))
      await new Promise(r => setTimeout(r, 400))

      setRefreshSteps(prev => prev.map((s, i) => i <= 1 ? { ...s, status: 'done' } : i === 2 ? { ...s, status: 'active' } : s))
      const data = await apiFetch<any>(`/cameras/${camera.id}/passport/refresh`, {
        method: 'POST',
        body: JSON.stringify({}),
      })

      setRefreshSteps(prev => prev.map((s, i) => i <= 2 ? { ...s, status: 'done' } : i === 3 ? { ...s, status: 'done', detail: `${data.profiles?.length || 0} profiles` } : i === 4 ? { ...s, status: 'active' } : s))
      await new Promise(r => setTimeout(r, 300))

      setRefreshSteps(prev => prev.map((s, i) => i <= 4 ? { ...s, status: 'done' } : i === 5 ? { ...s, status: 'done' } : i === 6 ? { ...s, status: 'active' } : s))
      await new Promise(r => setTimeout(r, 200))

      const hasConflicts = data.conflicts && data.conflicts.length > 0
      setRefreshSteps(prev => prev.map((s, i) => i <= 5 ? { ...s, status: 'done' } : i === 6 ? { ...s, status: hasConflicts ? 'error' : 'done', detail: hasConflicts ? `${data.conflicts.length} conflicts` : 'OK' } : i === 7 ? { ...s, status: 'active' } : s))

      if (data.profiles?.length) {
        setPassportProfiles(data.profiles)
      }
      if (data.ai_stream_profile_id) {
        setAiStreamProfileId(data.ai_stream_profile_id)
      }

      setRefreshSteps(prev => prev.map((s, i) => i <= 6 ? { ...s, status: 'done' } : { ...s, status: 'done', detail: data.ai_stream_profile_id ? 'AI stream validated' : 'no AI stream' }))

      if (data.success) {
        setAlertState({ isOpen: true, title: 'Готово', message: `Паспорт обновлён: ${data.vendor || ''} ${data.model || ''}` })
        onSaved()
      }
    } catch (e: any) {
      setRefreshSteps(prev => prev.map(s => s.status === 'active' ? { ...s, status: 'error' } : s))
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка обновления паспорта: ' + e.message })
    } finally {
      setRefreshRunning(false)
    }
  }

  async function handleSelectAiStream(profileId: string | null) {
    try {
      await apiFetch(`/cameras/${camera.id}/ai-stream`, {
        method: 'PUT',
        body: JSON.stringify({ profile_id: profileId }),
      })
      setAiStreamProfileId(profileId)
      setAlertState({ isOpen: true, title: 'Готово', message: profileId ? 'AI поток выбран' : 'AI поток сброшен' })
    } catch (e: any) {
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка выбора AI потока: ' + e.message })
    }
  }

  async function handlePopulateStreamSettings() {
    try {
      const data = await apiFetch<{ success: boolean; row1: StreamRow; row2: StreamRow; sourceLabel?: string; vendor?: string; model?: string }>(`/cameras/${camera.id}/stream-settings/populate`, {
        method: 'POST',
        body: JSON.stringify({}),
      })
      if (data.success) {
        setStreamSettings({ row1: data.row1, row2: data.row2 })
        setAlertState({ isOpen: true, title: 'Готово', message: `Параметры потоков получены (${data.sourceLabel || 'probe'})` })
      }
    } catch (e: any) {
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка заполнения: ' + e.message })
    }
  }

  async function handleSaveAll() {
    if (!name.trim()) { setError('Название обязательно'); return }
    if (!source.trim()) { setError('Источник обязателен'); return }
    setSaving(true)
    setError('')
    try {
      await apiFetch(`/cameras/${camera.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: name.trim(),
          source: source.trim(),
          zone: zone.trim() || null,
          is_smart_recording: smartRec,
          is_chronicle: chronicle,
          ip_address: ipAddress.trim() || null,
          ip_port: ipPort ? parseInt(ipPort) : null,
          username: username.trim() || null,
          password: password || null,
          use_camera_analytics: useAnalytics,
        }),
      })

      if (streamSettings) {
        await apiFetch(`/cameras/${camera.id}/stream-settings`, {
          method: 'PUT',
          body: JSON.stringify({ row1: streamSettings.row1, row2: streamSettings.row2 }),
        })
      }

      setAlertState({ isOpen: true, title: 'Готово', message: 'Все настройки сохранены' })
      onSaved()
    } catch (e: any) {
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка сохранения: ' + e.message })
    } finally {
      setSaving(false)
    }
  }

  async function handleStartStop() {
    try {
      if (camera.status === 'online') {
        await apiFetch(`/cameras/${camera.id}/stop`, { method: 'POST' })
      } else {
        await apiFetch(`/cameras/${camera.id}/start`, { method: 'POST' })
      }
      onSaved()
    } catch (e: any) {
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка: ' + e.message })
    }
  }

  const confidenceColor = (conf?: string | null) => {
    switch (conf) {
      case 'real': return 'text-kraken-green'
      case 'probed': return 'text-kraken-blue'
      case 'template': return 'text-kraken-orange'
      case 'manual': return 'text-kraken-muted'
      case 'conflict': return 'text-red-400'
      default: return 'text-kraken-muted'
    }
  }

  try {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
        <div className="panel w-full max-w-6xl mx-4 animate-fade-in max-h-[92vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>

          {/* Header */}
          <div className="flex items-start justify-between gap-4 border-b border-kraken-border px-6 py-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-kraken-text font-bold text-lg">{camera.name}</h2>
                <StatusBadge status={camera.status} />
                <span className="text-kraken-muted text-xs">ID {camera.id} · {camera.camera_type}</span>
              </div>
              <RtspLine url={camera.source} />
            </div>
            <button onClick={onClose} className="text-kraken-muted hover:text-kraken-text transition-colors flex-shrink-0">
              <X size={20} />
            </button>
          </div>

        {/* Error */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
            {error}
          </div>
        )}

        {/* Body: two columns, no tabs */}
        <div className="grid flex-1 grid-cols-12 gap-4 overflow-y-auto px-6 py-4">

          {/* Left column */}
          <div className="col-span-12 flex flex-col gap-4 lg:col-span-4">
            <Section title="Основные">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Название" className="col-span-2">
                  <input className={inputCls} value={name} onChange={e => setName(e.target.value)} placeholder="Название камеры" />
                </Field>
                <Field label="Зона">
                  <input className={inputCls} value={zone} onChange={e => setZone(e.target.value)} placeholder="Зона" />
                </Field>
                <Field label="FPS">
                  <input className={inputCls} value={camera.fps ?? ''} disabled placeholder="—" />
                </Field>
                <Field label="IP адрес" className="col-span-2">
                  <input className={inputCls + ' font-mono'} value={ipAddress} onChange={e => setIpAddress(e.target.value)} placeholder="192.168.1.100" />
                </Field>
                <Field label="IP порт">
                  <input className={inputCls + ' font-mono'} value={ipPort} onChange={e => setIpPort(e.target.value)} type="number" />
                </Field>
                <Field label="Ping">
                  <div className="py-2 text-xs text-kraken-text">{camera.ping_ms != null ? `${camera.ping_ms} ms` : '—'}</div>
                </Field>
                <Field label="Статус">
                  <div className="py-2"><StatusBadge status={camera.status} /></div>
                </Field>
              </div>

              <div className="mt-4 flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={smartRec} onChange={e => setSmartRec(e.target.checked)} className="rounded border-kraken-border bg-kraken-base text-kraken-purple focus:ring-kraken-purple" />
                  <span className="text-kraken-text text-xs">Умная запись</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={chronicle} onChange={e => setChronicle(e.target.checked)} className="rounded border-kraken-border bg-kraken-base text-kraken-purple focus:ring-kraken-purple" />
                  <span className="text-kraken-text text-xs">Хроника</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={useAnalytics} onChange={e => setUseAnalytics(e.target.checked)} className="rounded border-kraken-border bg-kraken-base text-kraken-purple focus:ring-kraken-purple" />
                  <span className="text-kraken-text text-xs">Аналитика</span>
                </label>
              </div>
            </Section>

            <Section
              title="Паспорт камеры"
              right={
                <button type="button" className={btnGhost} onClick={handleRefreshPassport} disabled={refreshRunning}>
                  <RefreshCw size={14} className={refreshRunning ? 'animate-spin' : ''} />
                  {refreshRunning ? 'Обновление...' : 'Обновить паспорт'}
                </button>
              }
            >
              <div className="grid grid-cols-2 gap-3 text-xs">
                {camera.vendor && (
                  <div>
                    <span className="text-kraken-muted text-[10px]">Производитель</span>
                    <div className="text-kraken-text font-medium">{camera.vendor}</div>
                  </div>
                )}
                {camera.model_name && (
                  <div>
                    <span className="text-kraken-muted text-[10px]">Модель</span>
                    <div className="text-kraken-text font-medium">{camera.model_name}</div>
                  </div>
                )}
                {camera.firmware && (
                  <div>
                    <span className="text-kraken-muted text-[10px]">Прошивка</span>
                    <div className="text-kraken-text font-mono">{camera.firmware}</div>
                  </div>
                )}
                {camera.serial_number && (
                  <div>
                    <span className="text-kraken-muted text-[10px]">Серийный номер</span>
                    <div className="text-kraken-text font-mono">{camera.serial_number}</div>
                  </div>
                )}
                {camera.mac_address && (
                  <div>
                    <span className="text-kraken-muted text-[10px]">MAC</span>
                    <div className="text-kraken-text font-mono">{camera.mac_address}</div>
                  </div>
                )}
                <div>
                  <span className="text-kraken-muted text-[10px]">ONVIF</span>
                  <div className="text-kraken-text">{camera.onvif_supported ? 'Да' : 'Нет'}</div>
                </div>
                <div>
                  <span className="text-kraken-muted text-[10px]">Данные</span>
                  <div className={`text-kraken-text font-medium ${confidenceColor(camera.data_confidence)}`}>
                    {camera.data_confidence || 'unknown'}
                  </div>
                </div>
                {camera.last_verified_at && (
                  <div className="col-span-2">
                    <span className="text-kraken-muted text-[10px]">Последняя проверка</span>
                    <div className="text-kraken-text font-mono">{new Date(camera.last_verified_at).toLocaleString()}</div>
                  </div>
                )}
              </div>

              <div className="mt-3">
                <span className={labelCls}>Возможности камеры</span>
                {passportProfiles.length > 0 ? (
                  <ul className="mt-1 space-y-1">
                    {passportProfiles.map((p: any) => {
                      const res = p.resolutions?.[0] || p
                      return (
                        <li key={p.id} className="rounded bg-kraken-base/80 px-2 py-1 font-mono text-[11px] text-kraken-text">
                          {p.name || p.id} — {res.label || `${res.width}x${res.height}`} — {p.codec || 'H.264'}
                        </li>
                      )
                    })}
                  </ul>
                ) : (
                  <p className="text-[11px] text-kraken-muted mt-1">Профили не обнаружены. Нажмите «Обновить паспорт».</p>
                )}
              </div>

              <div className="mt-3">
                <Field label="Активная конфигурация (AI STREAM)">
                  <select className={inputCls} value={aiStreamProfileId || ''} onChange={e => handleSelectAiStream(e.target.value || null)}>
                    <option value="">— не выбран —</option>
                    {passportProfiles.map((p: any) => {
                      const res = p.resolutions?.[0] || p
                      return (
                        <option key={p.id} value={p.id}>
                          {p.name || p.id} — {res.label || `${res.width}x${res.height}`} — {p.codec || 'H.264'}
                        </option>
                      )
                    })}
                  </select>
                </Field>
              </div>

              {refreshSteps.length > 0 && (
                <div className="mt-3 p-3 rounded-lg bg-kraken-base border border-kraken-border">
                  <div className="grid grid-cols-2 gap-2">
                    {refreshSteps.map((step, idx) => (
                      <div key={idx} className="flex items-center justify-between text-[10px]">
                        <span className="text-kraken-muted">{step.label}</span>
                        <span className={
                          step.status === 'done' ? 'text-kraken-green' :
                          step.status === 'error' ? 'text-red-400' :
                          step.status === 'active' ? 'text-kraken-blue' :
                          'text-kraken-muted'
                        }>
                          {step.status === 'done' ? '✓' : step.status === 'error' ? '✗' : step.status === 'active' ? '◌' : '○'}
                          {step.detail ? ` ${step.detail}` : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Section>
          </div>

          {/* Right column: streams */}
          <div className="col-span-12 lg:col-span-8">
            <Section
              title="Потоки"
              right={
                <button type="button" className={btnGhost} onClick={handlePopulateStreamSettings} disabled={streamLoading}>
                  <Search size={14} />
                  {streamLoading ? 'Заполнение...' : 'Заполнить из камеры'}
                </button>
              }
            >
              {streamLoading ? (
                <div className="text-kraken-muted text-xs text-center py-4">Загрузка...</div>
              ) : streamSettings ? (
                <div className="flex flex-col gap-3">
                  <StreamCard
                    title="Строка 1 — Основной поток"
                    row={streamSettings.row1}
                    listId="res-main"
                    canDisable={false}
                    onChange={(row1) => setStreamSettings({ ...streamSettings, row1 })}
                  />
                  <StreamCard
                    title="Строка 2 — Дополнительный поток"
                    row={streamSettings.row2}
                    listId="res-sub"
                    onChange={(row2) => setStreamSettings({ ...streamSettings, row2 })}
                  />
                </div>
              ) : (
                <div className="text-kraken-muted text-xs text-center py-4">
                  Нажмите «Заполнить из камеры» для получения параметров
                </div>
              )}
            </Section>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 border-t border-kraken-border px-6 py-4">
          <button
            type="button"
            className="flex-1 rounded-lg bg-kraken-purple hover:bg-kraken-purple-hover text-white text-sm font-semibold py-2.5 transition-colors disabled:opacity-50"
            onClick={handleSaveAll}
            disabled={saving}
          >
            <Save size={16} className="inline-block mr-2" />
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
          <button
            type="button"
            className="rounded-lg border border-kraken-border px-5 py-2.5 text-sm text-kraken-text hover:bg-kraken-hover transition-colors"
            onClick={handleStartStop}
          >
            {camera.status === 'online' ? <><Square size={16} className="inline-block mr-2 text-kraken-red" />Остановить</> : <><Play size={16} className="inline-block mr-2 text-kraken-green" />Запустить</>}
          </button>
        </div>

        {/* Alert Modal */}
        {alertState?.isOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setAlertState(null)}>
            <div className="panel p-6 w-full max-w-md mx-4 animate-fade-in" onClick={e => e.stopPropagation()}>
              <h3 className="text-kraken-text font-bold text-lg mb-2">{alertState.title}</h3>
              <p className="text-kraken-muted text-sm mb-4">{alertState.message}</p>
              <button onClick={() => setAlertState(null)} className="w-full btn-primary">
                OK
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
  } catch (e) {
    setRenderError(e instanceof Error ? e.message : String(e))
    return null
  }
}
