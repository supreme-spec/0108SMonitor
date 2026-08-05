import { useState, useEffect } from 'react'
import { X, Wifi, WifiOff, RefreshCw, Play, Square, Video, Settings2, Save, Search } from 'lucide-react'
import type { Camera } from '../types'
import { apiFetch } from '../api/client'

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

export default function CameraSettingsModal({ camera, onClose, onSaved }: CameraSettingsModalProps) {
  // Basic camera settings
  const [name, setName] = useState(camera.name)
  const [source, setSource] = useState(camera.source)
  const [zone, setZone] = useState(camera.zone ?? '')
  const [smartRec, setSmartRec] = useState(camera.is_smart_recording)
  const [chronicle, setChronicle] = useState(camera.is_chronicle)
  const [ipAddress, setIpAddress] = useState(camera.ip_address ?? '')
  const [ipPort, setIpPort] = useState(camera.ip_port?.toString() ?? '80')
  const [username, setUsername] = useState(camera.username ?? '')
  const [password, setPassword] = useState(camera.password ?? '')
  const [useAnalytics, setUseAnalytics] = useState(camera.use_camera_analytics ?? false)

  // Stream settings
  const [streamSettings, setStreamSettings] = useState<{ row1: StreamRow; row2: StreamRow } | null>(null)
  const [streamLoading, setStreamLoading] = useState(false)
  const [streamSaving, setStreamSaving] = useState(false)

  // Passport data
  const [passportProfiles, setPassportProfiles] = useState<any[]>([])
  const [aiStreamProfileId, setAiStreamProfileId] = useState<string | null>(null)
  const [refreshSteps, setRefreshSteps] = useState<Array<{ label: string; status: 'pending' | 'active' | 'done' | 'error'; detail?: string }>>([])
  const [refreshRunning, setRefreshRunning] = useState(false)

  // UI state
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [alertState, setAlertState] = useState<{ isOpen: boolean; title: string; message: string } | null>(null)

  const defaultRow: StreamRow = { codec: 'H.264', gop: 30, fps: camera.fps || 25, resolution: '1920x1080', bitrate: 4096, sourceLabel: 'manual' }

  // Load passport data
  useEffect(() => {
    loadPassportData()
  }, [camera.id, camera.stream_profiles])

  function loadPassportData() {
    const profiles = parsePassportProfiles(camera)
    setPassportProfiles(profiles)
    setAiStreamProfileId(camera.ai_stream_profile_id || null)
    
    // Load stream settings
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
    } catch (e) {
      // Use defaults if endpoint fails
      setStreamSettings({
        row1: defaultRow,
        row2: { ...defaultRow, bitrate: 2048, sourceLabel: 'manual' }
      })
    } finally {
      setStreamLoading(false)
    }
  }

  function getConfidenceColor(conf?: string | null): string {
    switch (conf) {
      case 'real': return 'text-kraken-green'
      case 'probed': return 'text-kraken-blue'
      case 'template': return 'text-kraken-orange'
      case 'manual': return 'text-kraken-gray'
      case 'conflict': return 'text-red-400'
      default: return 'text-kraken-muted'
    }
  }

  function getSourceLabelColor(source?: string | null): string {
    switch (source) {
      case 'onvif': return 'bg-kraken-green/20 text-kraken-green'
      case 'rtsp': return 'bg-kraken-blue/20 text-kraken-blue'
      case 'template': return 'bg-kraken-orange/20 text-kraken-orange'
      case 'manual': return 'bg-kraken-gray/20 text-kraken-gray'
      default: return 'bg-kraken-muted/20 text-kraken-muted'
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
        if (data.vendor || data.model) {
          setAlertState({ isOpen: true, title: 'Готово', message: `Определена камера: ${data.vendor || ''} ${data.model || ''}` })
        } else {
          setAlertState({ isOpen: true, title: 'Готово', message: `Параметры потоков получены (${data.sourceLabel || 'probe'})` })
        }
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
      // Save basic camera settings
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

      // Save stream settings if available
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

  const Section = ({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) => (
    <div className="p-4 rounded-xl bg-kraken-hover border border-kraken-border">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={16} className="text-kraken-purple" />
        <h3 className="text-kraken-text text-sm font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  )

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <label className="text-kraken-muted text-[10px] mb-1 block uppercase tracking-wider">{label}</label>
      {children}
    </div>
  )

  const Input = (props: any) => (
    <input
      {...props}
      className="w-full bg-kraken-base border border-kraken-border text-kraken-text text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple transition-colors"
    />
  )

  const Select = (props: any) => (
    <select
      {...props}
      className="w-full bg-kraken-base border border-kraken-border text-kraken-text text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple transition-colors"
    />
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="panel p-6 w-full max-w-4xl mx-4 animate-fade-in max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-kraken-text font-bold text-xl flex items-center gap-2">
              <Settings2 size={20} className="text-kraken-purple" />
              Настройки камеры
            </h2>
            <p className="text-kraken-muted text-xs mt-1">{camera.name} · ID {camera.id} · {camera.camera_type}</p>
          </div>
          <button onClick={onClose} className="text-kraken-muted hover:text-kraken-text transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Section 1: Basic Settings */}
          <Section title="Основные настройки" icon={Settings2}>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Название">
                <Input value={name} onChange={e => setName(e.target.value)} placeholder="Название камеры" />
              </Field>
              <Field label="Источник">
                <Input value={source} onChange={e => setSource(e.target.value)} placeholder="rtsp://..." className="font-mono text-[11px]" />
              </Field>
              <Field label="Зона">
                <Input value={zone} onChange={e => setZone(e.target.value)} placeholder="Зона расположения" />
              </Field>
              <Field label="Статус">
                <div className={`text-sm font-bold flex items-center gap-2 ${camera.status === 'online' ? 'text-kraken-green' : 'text-kraken-disabled'}`}>
                  {camera.status === 'online' ? <Wifi size={14} /> : <WifiOff size={14} />}
                  {camera.status === 'online' ? 'ОНЛАЙН' : camera.status === 'connecting' ? 'ПОДКЛЮЧЕНИЕ' : 'ОФЛАЙН'}
                </div>
              </Field>
              <Field label="IP адрес">
                <Input value={ipAddress} onChange={e => setIpAddress(e.target.value)} placeholder="192.168.1.100" className="font-mono" />
              </Field>
              <Field label="IP порт">
                <Input value={ipPort} onChange={e => setIpPort(e.target.value)} type="number" className="font-mono" />
              </Field>
              <Field label="Пользователь">
                <Input value={username} onChange={e => setUsername(e.target.value)} placeholder="username" />
              </Field>
              <Field label="Пароль">
                <Input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="••••••••" />
              </Field>
            </div>
            
            {/* Toggles */}
            <div className="flex gap-6 mt-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={smartRec}
                  onChange={e => setSmartRec(e.target.checked)}
                  className="w-4 h-4 rounded border-kraken-border bg-kraken-base text-kraken-purple focus:ring-kraken-purple"
                />
                <span className="text-kraken-text text-xs">Умная запись</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={chronicle}
                  onChange={e => setChronicle(e.target.checked)}
                  className="w-4 h-4 rounded border-kraken-border bg-kraken-base text-kraken-purple focus:ring-kraken-purple"
                />
                <span className="text-kraken-text text-xs">Хроника</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useAnalytics}
                  onChange={e => setUseAnalytics(e.target.checked)}
                  className="w-4 h-4 rounded border-kraken-border bg-kraken-base text-kraken-purple focus:ring-kraken-purple"
                />
                <span className="text-kraken-text text-xs">Аналитика</span>
              </label>
            </div>
          </Section>

          {/* Section 2: Camera Passport */}
          <Section title="Паспорт камеры" icon={Video}>
            <div className="grid grid-cols-3 gap-3 text-xs">
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
                <div className={`text-kraken-text font-medium ${getConfidenceColor(camera.data_confidence)}`}>
                  {camera.data_confidence || 'unknown'}
                </div>
              </div>
              {camera.last_verified_at && (
                <div className="col-span-3">
                  <span className="text-kraken-muted text-[10px]">Последняя проверка</span>
                  <div className="text-kraken-text font-mono">{new Date(camera.last_verified_at).toLocaleString()}</div>
                </div>
              )}
            </div>

            {/* AI Stream Selection */}
            {passportProfiles.length > 0 && (
              <div className="mt-4">
                <Field label="AI поток">
                  <Select
                    value={aiStreamProfileId || ''}
                    onChange={e => handleSelectAiStream(e.target.value || null)}
                  >
                    <option value="">Без AI потока</option>
                    {passportProfiles.map((p: any) => {
                      const res = p.resolutions?.[0] || p
                      return (
                        <option key={p.id} value={p.id}>
                          {p.name || p.id} — {res.label || `${res.width}x${res.height}`} — {p.codec || 'H.264'}
                        </option>
                      )
                    })}
                  </Select>
                </Field>
              </div>
            )}

            {/* Refresh Button */}
            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={handleRefreshPassport}
                disabled={refreshRunning}
                className="flex items-center gap-2 text-xs bg-kraken-purple/10 hover:bg-kraken-purple/20 text-kraken-purple px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw size={14} className={refreshRunning ? 'animate-spin' : ''} />
                {refreshRunning ? 'Обновление...' : 'Обновить паспорт'}
              </button>
              {camera.data_confidence && (
                <span className={`text-xs px-3 py-1 rounded-lg ${getConfidenceColor(camera.data_confidence)} bg-kraken-hover`}>
                  {camera.data_confidence}
                </span>
              )}
            </div>

            {/* Refresh Steps */}
            {refreshSteps.length > 0 && (
              <div className="mt-4 p-3 rounded-lg bg-kraken-base border border-kraken-border">
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

          {/* Section 3: Stream Settings */}
          <Section title="Настройки потоков" icon={Video}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-kraken-muted text-xs">Параметры активных окон</span>
              <button
                onClick={handlePopulateStreamSettings}
                disabled={streamLoading}
                className="flex items-center gap-2 text-xs bg-kraken-blue/10 hover:bg-kraken-blue/20 text-kraken-blue px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
              >
                <Search size={12} />
                Заполнить автоматически
              </button>
            </div>

            {streamLoading ? (
              <div className="text-kraken-muted text-xs text-center py-4">Загрузка...</div>
            ) : streamSettings ? (
              <div className="space-y-3">
                {[
                  { row: streamSettings.row1, label: 'Основной поток', setRow: (r: StreamRow) => setStreamSettings({ ...streamSettings, row1: r }) },
                  { row: streamSettings.row2, label: 'Дополнительный поток', setRow: (r: StreamRow) => setStreamSettings({ ...streamSettings, row2: r }) }
                ].map(({ row, label, setRow }) => (
                  <div key={label} className="border border-kraken-border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-kraken-text text-xs font-semibold">{label}</span>
                      {row.sourceLabel && (
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                          row.sourceLabel === 'probe' ? 'border-green-500/40 text-green-400 bg-green-500/10' :
                          row.sourceLabel === 'onvif' ? 'border-kraken-purple/40 text-kraken-purple bg-kraken-purple/10' :
                          row.sourceLabel === 'template' ? 'border-kraken-orange/40 text-kraken-orange bg-kraken-orange/10' :
                          row.sourceLabel === 'manual' ? 'border-kraken-muted/40 text-kraken-muted bg-kraken-muted/10' :
                          'border-kraken-red/40 text-kraken-red bg-kraken-red/10'
                        }`}>
                          {row.sourceLabel === 'probe' ? 'FFprobe' :
                           row.sourceLabel === 'onvif' ? 'ONVIF' :
                           row.sourceLabel === 'template' ? 'Шаблон' :
                           row.sourceLabel === 'manual' ? 'Ручной' : 'Неизвестно'}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-5 gap-2">
                      <div>
                        <Field label="Кодек">
                          <Select
                            value={row.codec}
                            onChange={e => setRow({ ...row, codec: e.target.value, sourceLabel: 'manual' })}
                          >
                            <option value="H.264">H.264</option>
                            <option value="H.265">H.265</option>
                          </Select>
                        </Field>
                      </div>
                      <div>
                        <Field label="GOP">
                          <Input
                            value={row.gop}
                            onChange={e => setRow({ ...row, gop: parseInt(e.target.value) || 0, sourceLabel: 'manual' })}
                            type="number"
                          />
                        </Field>
                      </div>
                      <div>
                        <Field label="FPS">
                          <Input
                            value={row.fps}
                            onChange={e => setRow({ ...row, fps: parseInt(e.target.value) || 0, sourceLabel: 'manual' })}
                            type="number"
                          />
                        </Field>
                      </div>
                      <div>
                        <Field label="Разрешение">
                          <Select
                            value={row.resolution}
                            onChange={e => setRow({ ...row, resolution: e.target.value, sourceLabel: 'manual' })}
                          >
                            <option value="1920x1080">1920x1080</option>
                            <option value="1280x720">1280x720</option>
                            <option value="3840x2160">3840×2160 (4K)</option>
                            <option value="2560x1440">2560×1440 (2K)</option>
                            <option value="640x480">640×480</option>
                          </Select>
                        </Field>
                      </div>
                      <div>
                        <Field label="Битрейт">
                          <Input
                            value={row.bitrate}
                            onChange={e => setRow({ ...row, bitrate: parseInt(e.target.value) || 0, sourceLabel: 'manual' })}
                            type="number"
                          />
                        </Field>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-kraken-muted text-xs text-center py-4">
                Нажмите "Заполнить автоматически" для получения параметров
              </div>
            )}
          </Section>

          {/* Section 4: Camera Control */}
          <Section title="Управление камерой" icon={camera.status === 'online' ? Square : Play}>
            <div className="flex gap-3">
              <button
                onClick={handleStartStop}
                className={`flex-1 flex items-center justify-center gap-2 text-sm py-3 rounded-lg transition-colors ${
                  camera.status === 'online'
                    ? 'bg-kraken-red/10 hover:bg-kraken-red/20 text-kraken-red'
                    : 'bg-kraken-green/10 hover:bg-kraken-green/20 text-kraken-green'
                }`}
              >
                {camera.status === 'online' ? <Square size={16} /> : <Play size={16} />}
                {camera.status === 'online' ? 'Остановить' : 'Запустить'}
              </button>
            </div>
          </Section>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-kraken-border">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-kraken-muted hover:text-kraken-text transition-colors"
          >
            Отмена
          </button>
          <button
            onClick={handleSaveAll}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 text-sm bg-kraken-purple hover:bg-kraken-purple/80 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={16} />
            {saving ? 'Сохранение...' : 'Сохранить все'}
          </button>
        </div>

        {/* Alert Modal */}
        {alertState && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setAlertState(null)}>
            <div className="panel p-6 w-full max-w-md mx-4 animate-fade-in" onClick={e => e.stopPropagation()}>
              <h3 className="text-kraken-text font-bold text-lg mb-2">{alertState.title}</h3>
              <p className="text-kraken-muted text-sm mb-4">{alertState.message}</p>
              <button
                onClick={() => setAlertState(null)}
                className="w-full btn-primary"
              >
                OK
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
