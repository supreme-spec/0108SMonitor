import { useState, useEffect, useCallback } from 'react'
import { Plus, Play, Square, Trash2, Search, X, Wifi, WifiOff, RefreshCw, ScanLine, Edit2, Video, Settings2 } from 'lucide-react'
import type { Camera } from '../types'
import { apiFetch } from '../api/client'
import RoiEditor from '../components/RoiEditor'
import ConfirmModal, { AlertModal } from '../components/ConfirmModal'

interface FoundUsb { index: number; source: string; name: string }
interface FoundIp { ip: string; port: number; source: string; rtsp_base?: string; common_paths?: string[]; type: string }

interface CamerasProps {
  onOpenCameraSettings?: (cameraId: number) => void
}

export default function Cameras({ onOpenCameraSettings }: CamerasProps) {
  const [cameras, setCameras] = useState<Camera[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [prefillSource, setPrefillSource] = useState('')
  const [prefillType, setPrefillType] = useState('USB')
  const [prefillName, setPrefillName] = useState('')

  const [scanning, setScanning] = useState(false)
  const [usbFound, setUsbFound] = useState<FoundUsb[]>([])

  const [onvifScanning, setOnvifScanning] = useState(false)
  const [onvifFound, setOnvifFound] = useState<FoundIp[]>([])
  const [onvifNetwork, setOnvifNetwork] = useState('192.168.1')

  // ROI editor state
  const [roiCamera, setRoiCamera] = useState<Camera | null>(null)

  // Camera detail view state
  const [detailCamera, setDetailCamera] = useState<Camera | null>(null)
  const [detailTab, setDetailTab] = useState<'general' | 'active-windows'>('general')
  const [streamSettings, setStreamSettings] = useState<{ row1: any; row2: any } | null>(null)
  const [streamLoading, setStreamLoading] = useState(false)
  const [streamSaving, setStreamSaving] = useState(false)

  // Camera Passport 2.0 state
  const [passportProfiles, setPassportProfiles] = useState<any[]>([])
  const [aiStreamProfileId, setAiStreamProfileId] = useState<string | null>(null)
  const [refreshSteps, setRefreshSteps] = useState<Array<{ label: string; status: 'pending' | 'active' | 'done' | 'error'; detail?: string }>>([])
  const [refreshRunning, setRefreshRunning] = useState(false)

  const [confirmState, setConfirmState] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    isDamage?: boolean;
  } | null>(null)
  const [alertState, setAlertState] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
  } | null>(null)

  const fetchCameras = useCallback(async () => {
    try {
      const data = await apiFetch<Camera[]>('/cameras')
      setCameras(data)
    } catch {}
    finally { setLoading(false) }
  }, [])

  function parsePassportProfiles(cam: Camera | null): any[] {
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

  function getSourceLabelText(source?: string | null): string {
    switch (source) {
      case 'onvif': return 'ONVIF'
      case 'rtsp': return 'RTSP'
      case 'template': return 'TEMPLATE'
      case 'manual': return 'MANUAL'
      default: return 'UNKNOWN'
    }
  }

  function getCodecColor(codec?: string): string {
    const c = (codec || '').toUpperCase()
    if (c.includes('H265') || c.includes('HEVC')) return 'text-kraken-purple'
    if (c.includes('H264') || c.includes('AVC')) return 'text-kraken-blue'
    if (c.includes('MPEG4')) return 'text-kraken-green'
    return 'text-kraken-text'
  }

  async function handleRefreshPassport() {
    if (!detailCamera || refreshRunning) return
    console.log(`[CLIENT] Обновление паспорта камеры: ${detailCamera.name} (id=${detailCamera.id})`)
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
      const data = await apiFetch<any>(`/cameras/${detailCamera.id}/passport/refresh`, {
        method: 'POST',
        body: JSON.stringify({}),
      })

      console.log(`[CLIENT] Ответ сервера (паспорт ${detailCamera.id}):`, {
        success: data.success,
        vendor: data.vendor,
        model: data.model,
        profilesCount: data.profiles?.length,
        conflictsCount: data.conflicts?.length,
        aiStreamProfileId: data.ai_stream_profile_id,
        dataConfidence: data.data_confidence,
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
        fetchCameras()
      }
    } catch (e: any) {
      console.error(`[CLIENT] Ошибка обновления паспорта камеры ${detailCamera?.id}:`, e.message)
      setRefreshSteps(prev => prev.map(s => s.status === 'active' ? { ...s, status: 'error' } : s))
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка обновления паспорта: ' + e.message })
    } finally {
      setRefreshRunning(false)
    }
  }

  async function handleSelectAiStream(profileId: string | null) {
    if (!detailCamera) return
    try {
      await apiFetch(`/cameras/${detailCamera.id}/ai-stream`, {
        method: 'PUT',
        body: JSON.stringify({ profile_id: profileId }),
      })
      setAiStreamProfileId(profileId)
      setAlertState({ isOpen: true, title: 'Готово', message: profileId ? 'AI поток выбран' : 'AI поток сброшен' })
    } catch (e: any) {
      setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка выбора AI потока: ' + e.message })
    }
  }

  function loadPassportData(cam: Camera | null) {
    if (!cam) {
      setPassportProfiles([])
      setAiStreamProfileId(null)
      return
    }
    const profiles = parsePassportProfiles(cam)
    setPassportProfiles(profiles)
    setAiStreamProfileId(cam.ai_stream_profile_id || null)
  }

  useEffect(() => {
    if (detailCamera) loadPassportData(detailCamera)
  }, [detailCamera?.id, detailCamera?.stream_profiles])

  useEffect(() => {
    fetchCameras()
    const t = setInterval(() => {
      if (!document.hidden) fetchCameras()
    }, 3000)
    return () => clearInterval(t)
  }, [fetchCameras])

  const handleStart = async (id: number) => {
    await apiFetch(`/cameras/${id}/start`, { method: 'POST' })
    fetchCameras()
  }

  const handleStop = async (id: number) => {
    await apiFetch(`/cameras/${id}/stop`, { method: 'POST' })
    fetchCameras()
  }

  const handleDelete = (id: number) => {
    setConfirmState({
      isOpen: true,
      title: 'Удалить камеру',
      message: 'Удалить эту камеру?',
      isDamage: true,
      onConfirm: async () => {
        setConfirmState(null)
        try {
          await apiFetch(`/cameras/${id}`, { method: 'DELETE' })
          fetchCameras()
        } catch (e: any) {
          setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка удаления: ' + e.message })
        }
      }
    })
  }

  const openCameraDetail = async (cam: Camera) => {
    setDetailCamera(cam)
    setDetailTab('general')
    setStreamLoading(true)
    try {
      const data = await apiFetch<{ row1: any; row2: any }>(`/cameras/${cam.id}/stream-settings`)
      setStreamSettings(data)
    } catch { setStreamSettings({ row1: null, row2: null }) }
    finally { setStreamLoading(false) }
  }

  const handleRecord = async (id: number) => {
    try {
      await apiFetch(`/recordings/start/${id}`, { method: 'POST' })
      setAlertState({ isOpen: true, title: 'Запись запущена', message: 'Запись запущена на 15 секунд' })
    } catch (e: any) {
      setAlertState({ isOpen: true, title: 'Ошибка записи', message: e.message })
    }
  }

  const handleScanUSB = async () => {
    setScanning(true)
    setUsbFound([])
    try {
      const res = await apiFetch<{ cameras: FoundUsb[] }>('/cameras/scan/usb')
      setUsbFound(res.cameras)
    } catch {}
    finally { setScanning(false) }
  }

  const handleScanONVIF = async () => {
    setOnvifScanning(true)
    setOnvifFound([])
    try {
      const res = await apiFetch<{ cameras: FoundIp[] }>(`/cameras/scan/onvif?network=${onvifNetwork}`)
      setOnvifFound(res.cameras)
    } catch {}
    finally { setOnvifScanning(false) }
  }

  const openAddWithPreset = (source: string, type: string, name: string) => {
    setPrefillSource(source)
    setPrefillType(type)
    setPrefillName(name)
    setShowAdd(true)
  }

  const statusColor = (s: string) => {
    if (s === 'online') return 'text-kraken-green'
    if (s === 'connecting' || s === 'reconnecting') return 'text-yellow-400'
    return 'text-kraken-disabled'
  }

  const statusLabel = (s: string) => ({
    online: 'ОНЛАЙН', offline: 'ОФЛАЙН',
    connecting: 'ПОДКЛЮЧЕНИЕ', reconnecting: 'ПЕРЕПОДКЛЮЧЕНИЕ',
  }[s] ?? s.toUpperCase())

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto">

      {/* ── Toolbar ── */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={() => { setPrefillSource(''); setPrefillType('USB'); setPrefillName(''); setShowAdd(true) }}
          className="btn-primary flex items-center gap-2 ml-auto"
        >
          <Plus size={16} />
          Добавить камеру
        </button>
      </div>

      {/* ── USB scan results ── */}
      {usbFound.length > 0 && (
        <div className="panel p-3">
          <div className="text-kraken-muted text-xs uppercase tracking-widest mb-2">Найдены USB камеры</div>
          <div className="flex flex-wrap gap-2">
            {usbFound.map(c => (
              <button
                key={c.source}
                onClick={() => openAddWithPreset(c.source, 'USB', `USB Camera ${c.index}`)}
                className="flex items-center gap-2 bg-kraken-hover hover:bg-kraken-purple/20 border border-kraken-border hover:border-kraken-purple px-3 py-1.5 rounded-lg text-sm transition-colors"
              >
                <span className="text-kraken-green">●</span>
                <span className="text-kraken-text">{c.name}</span>
                <span className="text-kraken-muted text-xs">index {c.source}</span>
                <Plus size={12} className="text-kraken-purple" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── ONVIF/IP scan results ── */}
      {onvifFound.length > 0 && (
        <div className="panel p-3">
          <div className="text-kraken-muted text-xs uppercase tracking-widest mb-2">
            Найдены IP камеры ({onvifFound.length})
          </div>
          <div className="flex flex-col gap-2">
            {onvifFound.map((c, i) => (
              <div key={i} className="flex items-center gap-3 bg-kraken-hover rounded-lg px-3 py-2">
                <div className="flex-1">
                  <div className="text-kraken-text text-sm font-medium">{c.ip}:{c.port}</div>
                  <div className="text-kraken-muted text-xs font-mono">{c.source}</div>
                  {c.common_paths && (
                    <div className="text-kraken-disabled text-xs mt-0.5">
                      Попробуйте пути: {c.common_paths.slice(0, 2).join(', ')}
                    </div>
                  )}
                </div>
                <span className="text-xs bg-kraken-blue/20 text-kraken-blue px-2 py-0.5 rounded">
                  {c.type}
                </span>
                <button
                  onClick={() => openAddWithPreset(c.source, 'RTSP', `IP Camera ${c.ip}`)}
                  className="flex items-center gap-1 bg-kraken-purple hover:bg-kraken-purple-hover text-white text-xs px-2 py-1 rounded-lg transition-colors"
                >
                  <Plus size={12} />
                  Добавить
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

{/* ── Camera grid ── */}
       <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-4">
        {loading && (
          <div className="col-span-3 text-center py-8 text-kraken-disabled">Загрузка...</div>
        )}
        {!loading && cameras.length === 0 && (
          <div className="col-span-3 text-center py-8 text-kraken-disabled">
            Камеры не добавлены. Нажмите "Найти USB" или "Добавить камеру".
          </div>
        )}
        {cameras.map(cam => (
          <div key={cam.id} className="panel p-4 flex flex-col gap-3 cursor-pointer hover:border-kraken-purple/50 transition-colors" onClick={() => openCameraDetail(cam)}>
            {/* Header: name + status */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="text-kraken-text font-semibold truncate">{cam.name}</div>
                {/* Source path — full text, wraps, monospace */}
                <div
                  className="text-kraken-muted text-xs mt-0.5 font-mono break-all leading-relaxed"
                  title={cam.source}
                >
                  {cam.source}
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                {cam.status === 'online'
                  ? <Wifi size={14} className="text-kraken-green" />
                  : cam.status === 'connecting' || cam.status === 'reconnecting'
                    ? <RefreshCw size={14} className="text-yellow-400 animate-spin" />
                    : <WifiOff size={14} className="text-kraken-disabled" />
                }
                <span className={`text-xs font-bold ${statusColor(cam.status)}`}>
                  {statusLabel(cam.status)}
                </span>
              </div>
            </div>

            {/* Badges */}
            <div className="flex items-center gap-2 flex-wrap text-xs text-kraken-muted">
              <span className="bg-kraken-hover px-2 py-0.5 rounded">{cam.camera_type}</span>
              {cam.vendor && <span className="bg-kraken-blue/10 text-kraken-blue px-2 py-0.5 rounded">{cam.vendor}</span>}
              {cam.model_name && <span className="bg-kraken-hover px-2 py-0.5 rounded text-kraken-text">{cam.model_name}</span>}
              {cam.zone && <span className="bg-kraken-hover px-2 py-0.5 rounded">{cam.zone}</span>}
              {cam.status === 'online' && cam.fps != null && (
                <span className="bg-kraken-hover px-2 py-0.5 rounded text-kraken-green font-mono">
                  {cam.fps} fps
                </span>
              )}
              {cam.status === 'online' && cam.ping_ms != null && (
                <span className={`px-2 py-0.5 rounded font-mono ${
                  cam.ping_ms < 50  ? 'bg-kraken-green/10 text-kraken-green' :
                  cam.ping_ms < 150 ? 'bg-yellow-400/10 text-yellow-400' :
                                      'bg-kraken-red/10 text-kraken-red'
                }`}>
                  {cam.ping_ms} ms
                </span>
              )}
              {cam.roi_zones && cam.roi_zones.length > 0 && (
                <span
                  className="bg-kraken-purple/20 text-kraken-purple px-2 py-0.5 rounded cursor-pointer hover:bg-kraken-purple/30 transition-colors"
                  onClick={() => setRoiCamera(cam)}
                  title="Настроить зоны детектирования"
                >
                  {cam.roi_zones.length} {cam.roi_zones.length === 1 ? 'зона' : cam.roi_zones.length < 5 ? 'зоны' : 'зон'}
                </span>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 mt-1">
              {cam.status !== 'online' ? (
                <button
                  onClick={() => handleStart(cam.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 bg-kraken-green/10 hover:bg-kraken-green/20 text-kraken-green text-sm py-1.5 rounded-lg transition-colors"
                >
                  <Play size={13} />
                  Запустить
                </button>
              ) : (
                <>
                  <button
                    onClick={() => handleStop(cam.id)}
                    className="flex-1 flex items-center justify-center gap-1.5 bg-kraken-red/10 hover:bg-kraken-red/20 text-kraken-red text-sm py-1.5 rounded-lg transition-colors"
                  >
                    <Square size={13} />
                    Остановить
                  </button>
                  <button
                    onClick={() => handleRecord(cam.id)}
                    className="flex items-center justify-center gap-1.5 bg-kraken-purple/10 hover:bg-kraken-purple/20 text-kraken-purple text-sm py-1.5 px-3 rounded-lg transition-colors"
                    title="Записать 15 секунд (умная съёмка)"
                  >
                    <Video size={13} />
                  </button>
                </>
              )}
              <button
                onClick={() => onOpenCameraSettings?.(cam.id)}
                className="p-1.5 rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-blue transition-colors"
                title="Настройки камеры"
              >
                <Settings2 size={14} />
              </button>
              <button
                onClick={() => setRoiCamera(cam)}
                className="p-1.5 rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-purple transition-colors"
                title="Зоны детектирования"
              >
                <ScanLine size={14} />
              </button>
              <button
                onClick={() => handleDelete(cam.id)}
                className="p-1.5 rounded-lg hover:bg-kraken-hover text-kraken-muted hover:text-kraken-red transition-colors"
                title="Удалить"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ── Add camera modal ── */}
      {showAdd && (
        <AddCameraModal
          onClose={() => setShowAdd(false)}
          onSaved={() => { setShowAdd(false); fetchCameras() }}
          usbFound={usbFound}
          initialSource={prefillSource}
          initialType={prefillType}
          initialName={prefillName}
        />
      )}

      {/* ── ROI zone editor ── */}
      {roiCamera && (
        <RoiEditor
          cameraId={roiCamera.id}
          cameraName={roiCamera.name}
          onClose={() => { setRoiCamera(null); fetchCameras() }}
        />
      )}

      {confirmState && (
        <ConfirmModal
          isOpen={confirmState.isOpen}
          title={confirmState.title}
          message={confirmState.message}
          isDamage={confirmState.isDamage}
          onConfirm={confirmState.onConfirm}
          onCancel={() => setConfirmState(null)}
        />
      )}

{alertState && (
        <AlertModal
          isOpen={alertState.isOpen}
          title={alertState.title}
          message={alertState.message}
          onClose={() => setAlertState(null)}
        />
      )}

      {/* ── Camera Detail Modal ── */}
      {detailCamera && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setDetailCamera(null)}>
          <div className="panel p-6 w-full max-w-2xl mx-4 animate-fade-in max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-kraken-text font-bold text-lg">{detailCamera.name}</h2>
                <p className="text-kraken-muted text-xs mt-0.5">{detailCamera.camera_type} · ID {detailCamera.id} · {detailCamera.source}</p>
              </div>
              <button onClick={() => setDetailCamera(null)} className="text-kraken-muted hover:text-kraken-text">
                <X size={18} />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mb-4 border-b border-kraken-border">
              <button
                onClick={() => setDetailTab('general')}
                className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                  detailTab === 'general'
                    ? 'border-kraken-purple text-kraken-purple'
                    : 'border-transparent text-kraken-muted hover:text-kraken-text'
                }`}
              >
                Общие
              </button>
              <button
                onClick={() => setDetailTab('active-windows')}
                className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                  detailTab === 'active-windows'
                    ? 'border-kraken-purple text-kraken-purple'
                    : 'border-transparent text-kraken-muted hover:text-kraken-text'
                }`}
              >
                Активные окна
              </button>
            </div>

            {/* General Tab */}
            {detailTab === 'general' && (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-kraken-muted text-xs mb-1 block">Название</label>
                    <div className="text-kraken-text text-sm">{detailCamera.name}</div>
                  </div>
                  <div>
                    <label className="text-kraken-muted text-xs mb-1 block">Тип</label>
                    <div className="text-kraken-text text-sm">{detailCamera.camera_type}</div>
                  </div>
                  <div>
                    <label className="text-kraken-muted text-xs mb-1 block">Источник</label>
                    <div className="text-kraken-text text-sm font-mono break-all">{detailCamera.source}</div>
                  </div>
                  <div>
                    <label className="text-kraken-muted text-xs mb-1 block">Статус</label>
                    <div className={`text-sm font-bold ${detailCamera.status === 'online' ? 'text-kraken-green' : 'text-kraken-disabled'}`}>
                      {detailCamera.status === 'online' ? 'ОНЛАЙН' : detailCamera.status === 'connecting' ? 'ПОДКЛЮЧЕНИЕ' : 'ОФЛАЙН'}
                    </div>
                  </div>
                  {detailCamera.zone && (
                    <div>
                      <label className="text-kraken-muted text-xs mb-1 block">Зона</label>
                      <div className="text-kraken-text text-sm">{detailCamera.zone}</div>
                    </div>
                  )}
                  {detailCamera.fps != null && (
                    <div>
                      <label className="text-kraken-muted text-xs mb-1 block">FPS</label>
                      <div className="text-kraken-text text-sm">{detailCamera.fps}</div>
                    </div>
                  )}
                  {detailCamera.ping_ms != null && (
                    <div>
                      <label className="text-kraken-muted text-xs mb-1 block">Ping</label>
                      <div className="text-kraken-text text-sm">{detailCamera.ping_ms} ms</div>
                    </div>
                  )}
                </div>
                <div className="flex gap-3 mt-2">
                  {detailCamera.status !== 'online' ? (
                    <button onClick={() => { handleStart(detailCamera.id); setDetailCamera(null) }} className="btn-primary flex-1">Запустить</button>
                  ) : (
                    <button onClick={() => { handleStop(detailCamera.id); setDetailCamera(null) }} className="flex-1 bg-kraken-red/10 hover:bg-kraken-red/20 text-kraken-red text-sm py-2 rounded-lg transition-colors">Остановить</button>
                  )}
                  <button onClick={() => { setDetailCamera(null); onOpenCameraSettings?.(detailCamera.id) }} className="btn-ghost flex-1">Редактировать</button>
                </div>

                {/* Camera Passport 2.0 */}
                <div className="mt-3 space-y-3">
                  {/* Layer 1: Identity */}
                  <div className="p-3 rounded-lg bg-kraken-hover border border-kraken-border">
                    <div className="text-kraken-text text-xs font-semibold mb-2">🪪 Идентификация</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {detailCamera.vendor && (
                        <div>
                          <span className="text-kraken-muted text-[10px]">Производитель</span>
                          <div className="text-kraken-text">{detailCamera.vendor}</div>
                        </div>
                      )}
                      {detailCamera.model_name && (
                        <div>
                          <span className="text-kraken-muted text-[10px]">Модель</span>
                          <div className="text-kraken-text">{detailCamera.model_name}</div>
                        </div>
                      )}
                      {detailCamera.firmware && (
                        <div>
                          <span className="text-kraken-muted text-[10px]">Прошивка</span>
                          <div className="text-kraken-text font-mono">{detailCamera.firmware}</div>
                        </div>
                      )}
                      {detailCamera.serial_number && (
                        <div>
                          <span className="text-kraken-muted text-[10px]">Серийный номер</span>
                          <div className="text-kraken-text font-mono">{detailCamera.serial_number}</div>
                        </div>
                      )}
                      {detailCamera.mac_address && (
                        <div>
                          <span className="text-kraken-muted text-[10px]">MAC</span>
                          <div className="text-kraken-text font-mono">{detailCamera.mac_address}</div>
                        </div>
                      )}
                      <div>
                        <span className="text-kraken-muted text-[10px]">ONVIF</span>
                        <div className="text-kraken-text">{detailCamera.onvif_supported ? 'Да' : 'Нет'}</div>
                      </div>
                      <div>
                        <span className="text-kraken-muted text-[10px]">Данные</span>
                        <div className={`text-kraken-text ${getConfidenceColor(detailCamera.data_confidence)}`}>
                          {detailCamera.data_confidence || 'unknown'}
                        </div>
                      </div>
                      {detailCamera.last_verified_at && (
                        <div className="col-span-2">
                          <span className="text-kraken-muted text-[10px]">Последняя проверка</span>
                          <div className="text-kraken-text font-mono">{new Date(detailCamera.last_verified_at).toLocaleString()}</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Layer 2: Capabilities */}
                  <div className="p-3 rounded-lg bg-kraken-hover border border-kraken-border">
                    <div className="text-kraken-text text-xs font-semibold mb-2">⚙ Возможности камеры</div>
                    {passportProfiles.length === 0 ? (
                      <div className="text-kraken-muted text-xs">Профили не обнаружены. Нажмите «Обновить паспорт».</div>
                    ) : (
                      <div className="space-y-2">
                        {(() => {
                          const groups = passportProfiles.reduce((acc: any, p: any) => {
                            const type = p.type || (p.name?.toLowerCase().includes('main') ? 'main' : 'sub')
                            if (!acc[type]) acc[type] = []
                            acc[type].push(p)
                            return acc
                          }, {})
                          return Object.entries(groups).map(([type, profiles]: [string, any]) => (
                            <div key={type}>
                              <div className="text-kraken-muted text-[10px] uppercase tracking-wider mb-1">{type === 'main' ? 'MAIN STREAM' : 'SUB STREAM'}</div>
                              <div className="flex flex-wrap gap-2">
                                {(profiles as any[]).map((p: any, idx: number) => {
                                  const res = p.resolutions?.[0] || p
                                  const label = res.label || `${res.width}x${res.height}`
                                  return (
                                    <div key={idx} className="flex items-center gap-1.5 bg-kraken-base border border-kraken-border rounded-md px-2 py-1 text-xs">
                                      <span className="text-kraken-green">✓</span>
                                      <span className="text-kraken-text">{label}</span>
                                      <span className={`text-[10px] ${getCodecColor(p.codec)}`}>{p.codec || 'H.264'}</span>
                                      {p.fps?.current ? <span className="text-kraken-muted text-[10px]">{p.fps.current} FPS</span> : null}
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                          ))
                        })()}
                      </div>
                    )}
                  </div>

                  {/* Layer 3: Active Configuration */}
                  <div className="p-3 rounded-lg bg-kraken-hover border border-kraken-border">
                    <div className="text-kraken-text text-xs font-semibold mb-2">🎯 Активная конфигурация</div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-kraken-muted text-xs">AI STREAM</span>
                        <div className="flex items-center gap-2">
                          {aiStreamProfileId && passportProfiles.find((p: any) => p.id === aiStreamProfileId) ? (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${getSourceLabelColor((passportProfiles.find((p: any) => p.id === aiStreamProfileId) as any)?.source)}`}>
                              {getSourceLabelText((passportProfiles.find((p: any) => p.id === aiStreamProfileId) as any)?.source)}
                            </span>
                          ) : null}
                          <select
                            value={aiStreamProfileId || ''}
                            onChange={e => handleSelectAiStream(e.target.value || null)}
                            className="bg-kraken-base border border-kraken-border text-kraken-text text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-kraken-purple"
                          >
                            <option value="">— не выбран —</option>
                            {passportProfiles.map((p: any) => {
                              const res = p.resolutions?.[0] || p
                              const isRecommended = p.id === (detailCamera as any)?.recommended_ai_profile
                              return (
                                <option key={p.id} value={p.id}>
                                  {p.name || p.id} — {res.label || `${res.width}x${res.height}`} — {p.codec || 'H.264'} {isRecommended ? ' (рекомендуемый)' : ''}
                                </option>
                              )
                            })}
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Refresh Passport */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleRefreshPassport}
                      disabled={refreshRunning}
                      className="text-[10px] bg-kraken-purple/10 hover:bg-kraken-purple/20 text-kraken-purple px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {refreshRunning ? 'Обновление...' : '🔄 Обновить паспорт'}
                    </button>
                    {detailCamera.data_confidence && (
                      <span className={`text-[10px] px-2 py-1 rounded-lg ${getConfidenceColor(detailCamera.data_confidence)} bg-kraken-hover`}>
                        {detailCamera.data_confidence}
                      </span>
                    )}
                  </div>

                  {/* Refresh Pipeline Steps */}
                  {refreshSteps.length > 0 && (
                    <div className="p-2 rounded-lg bg-kraken-base border border-kraken-border space-y-1">
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
                  )}
                </div>
              </div>
            )}

            {/* Active Windows Tab */}
            {detailTab === 'active-windows' && (
              <ActiveWindowsTab
                key={detailCamera.id}
                camera={detailCamera}
                settings={streamSettings}
                loading={streamLoading}
                saving={streamSaving}
                onSave={async (row1, row2) => {
                  setStreamSaving(true)
                  try {
                    await apiFetch(`/cameras/${detailCamera.id}/stream-settings`, {
                      method: 'PUT',
                      body: JSON.stringify({ row1, row2 }),
                    })
                    setStreamSettings({ row1, row2 })
                    setAlertState({ isOpen: true, title: 'Готово', message: 'Параметры потоков сохранены' })
                  } catch (e: any) {
                    setAlertState({ isOpen: true, title: 'Ошибка', message: 'Ошибка сохранения: ' + e.message })
                  } finally {
                    setStreamSaving(false)
                  }
                }}
                onPopulate={async () => {
                  try {
                    const data = await apiFetch<{ success: boolean; row1: any; row2: any; sourceLabel?: string; vendor?: string; model?: string }>(`/cameras/${detailCamera.id}/stream-settings/populate`, {
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
                }}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}


// ── Add Camera Modal ──────────────────────────────────────────────────────────

interface AddModalProps {
  onClose: () => void
  onSaved: () => void
  usbFound: FoundUsb[]
  initialSource?: string
  initialType?: string
  initialName?: string
}

function AddCameraModal({ onClose, onSaved, usbFound, initialSource = '', initialType = 'USB', initialName = '' }: AddModalProps) {
  const [name, setName] = useState(initialName)
  const [source, setSource] = useState(initialSource)
  const [type, setType] = useState(initialType)
  const [zone, setZone] = useState('')
  const [smartRec, setSmartRec] = useState(false)
  const [chronicle, setChronicle] = useState(true)
  const [ipAddress, setIpAddress] = useState('')
  const [ipPort, setIpPort] = useState('80')
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [useAnalytics, setUseAnalytics] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const validateSource = () => {
    if (!source.trim()) return 'Источник обязателен'
    // Для USB-камер принимаем как числовые индексы (0,1,2), так и пути к устройствам (/dev/video0)
    if (type === 'USB') {
      const trimmed = source.trim()
      // Разрешаем: только цифры, или путь вида /dev/video*, или любой другой путь
      const isValid = /^\d+$/.test(trimmed) || /^\/dev\/video\d+$/.test(trimmed) || trimmed.includes('/') || trimmed.includes('\\')
      if (!isValid) {
        return 'USB источник должен быть числом (0, 1, 2...) или путем к устройству (/dev/video0)'
      }
    }
    return null
  }

  const handleSave = async () => {
    if (!name.trim()) { setError('Название обязательно'); return }
    const srcError = validateSource()
    if (srcError) { setError(srcError); return }

    setSaving(true)
    setError('')
    try {
      await apiFetch('/cameras', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim(),
          source: source.trim(),
          camera_type: type,
          driver_type: type === 'UNV' ? 'unv' : type === 'Hikvision' ? 'hikvision' : type === 'ONVIF' ? 'onvif' : null,
          zone: zone.trim(),
          is_smart_recording: smartRec,
          is_chronicle: chronicle,
          ip_address: ipAddress.trim() || null,
          ip_port: ipPort ? parseInt(ipPort) : null,
          username: username.trim() || null,
          password: password || null,
          use_camera_analytics: useAnalytics,
        }),
      })
      onSaved()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="panel p-6 w-full max-w-md mx-4 animate-fade-in max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-kraken-text font-bold text-lg">Добавить камеру</h2>
          <button onClick={onClose} className="text-kraken-muted hover:text-kraken-text">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <label className="text-kraken-muted text-xs mb-1 block">Название *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Главный вход"
              className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple"
            />
          </div>

          <div>
            <label className="text-kraken-muted text-xs mb-1 block">Тип</label>
            <select
              value={type}
              onChange={e => { setType(e.target.value); setSource('') }}
              className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple"
            >
              <option value="USB">USB (встроенная / USB камера)</option>
              <option value="RTSP">RTSP (IP камера)</option>
              <option value="IP">IP (HTTP поток)</option>
              <option value="Hikvision">Hikvision (ISAPI)</option>
              <option value="UNV">UNV (Uniview LAPI)</option>
              <option value="ONVIF">ONVIF (универсальный)</option>
            </select>
          </div>

          <div>
            <label className="text-kraken-muted text-xs mb-1 block">
              {type === 'USB' ? 'Индекс камеры (0, 1, 2...)' : 'RTSP URL'}
            </label>
            {usbFound.length > 0 && type === 'USB' ? (
              <select
                value={source}
                onChange={e => setSource(e.target.value)}
                className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple"
              >
                <option value="">Выберите камеру</option>
                {usbFound.map(c => (
                  <option key={c.index} value={c.source}>{c.name} (index {c.source})</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={source}
                onChange={e => setSource(e.target.value)}
                placeholder={type === 'USB' ? '0' : 'rtsp://admin:password@192.168.1.100:554/stream'}
                className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple font-mono"
              />
            )}
            {(type === 'RTSP' || type === 'IP') && (
              <div className="mt-1.5 text-kraken-disabled text-xs space-y-0.5">
                <div>Примеры RTSP путей:</div>
                <div className="font-mono">rtsp://admin:pass@192.168.1.100:554/stream</div>
                <div className="font-mono">rtsp://192.168.1.100:554/Streaming/Channels/101 (Hikvision)</div>
                <div className="font-mono">rtsp://192.168.1.100:554/cam/realmonitor?channel=1 (Dahua)</div>
              </div>
            )}
          </div>

          <div>
            <label className="text-kraken-muted text-xs mb-1 block">Зона (необязательно)</label>
            <input
              type="text"
              value={zone}
              onChange={e => setZone(e.target.value)}
              placeholder="Главный вход, Парковка..."
              className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple"
            />
          </div>

          {/* IP Camera fields — shown for non-USB types */}
          {type !== 'USB' && (
            <div className="border border-kraken-border rounded-xl p-3 space-y-3">
              <div className="text-kraken-muted text-xs uppercase tracking-widest">IP камера</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-kraken-muted text-[10px] mb-0.5 block">IP адрес</label>
                  <input type="text" value={ipAddress} onChange={e => setIpAddress(e.target.value)}
                    placeholder="192.168.1.100"
                    className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple font-mono" />
                </div>
                <div>
                  <label className="text-kraken-muted text-[10px] mb-0.5 block">Порт</label>
                  <input type="text" value={ipPort} onChange={e => setIpPort(e.target.value)}
                    placeholder="80"
                    className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple font-mono" />
                </div>
                <div>
                  <label className="text-kraken-muted text-[10px] mb-0.5 block">Логин</label>
                  <input type="text" value={username} onChange={e => setUsername(e.target.value)}
                    placeholder="admin"
                    className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple" />
                </div>
                <div>
                  <label className="text-kraken-muted text-[10px] mb-0.5 block">Пароль</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                    placeholder="••••••"
                    className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple" />
                </div>
              </div>
              {(type === 'Hikvision' || type === 'UNV') && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={useAnalytics} onChange={e => setUseAnalytics(e.target.checked)}
                    className="w-3.5 h-3.5 rounded border-kraken-border text-kraken-purple focus:ring-kraken-purple" />
                  <div className="flex flex-col">
                    <span className="text-kraken-text text-[10px] font-semibold">Аналитика камеры</span>
                    <span className="text-[9px] text-kraken-disabled">Использовать AI камеры вместо Kraken AI</span>
                  </div>
                </label>
              )}
            </div>
          )}

          <div className="flex gap-4 p-3 bg-kraken-base rounded-xl border border-kraken-border">
            <label className="flex-1 flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={smartRec}
                onChange={e => setSmartRec(e.target.checked)}
                className="w-4 h-4 rounded border-kraken-border text-kraken-purple focus:ring-kraken-purple"
              />
              <div className="flex flex-col">
                <span className="text-kraken-text text-xs font-semibold group-hover:text-kraken-purple transition-colors">Умная съёмка</span>
                <span className="text-[10px] text-kraken-disabled">Запись 15с при обнаружении</span>
              </div>
            </label>
            <div className="w-px bg-kraken-border h-8 self-center" />
            <label className="flex-1 flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={chronicle}
                onChange={e => setChronicle(e.target.checked)}
                className="w-4 h-4 rounded border-kraken-border text-kraken-purple focus:ring-kraken-purple"
              />
              <div className="flex flex-col">
                <span className="text-kraken-text text-xs font-semibold group-hover:text-kraken-purple transition-colors">Фотохроника</span>
                <span className="text-[10px] text-kraken-disabled">Снимок посетителя в день</span>
              </div>
            </label>
          </div>

          {error && <div className="text-kraken-red text-sm bg-kraken-red/10 px-3 py-2 rounded-lg">{error}</div>}

          <div className="flex gap-3 mt-2">
            <button onClick={onClose} className="btn-ghost flex-1">Отмена</button>
            <button onClick={handleSave} disabled={saving} className="btn-primary flex-1">
              {saving ? 'Добавление...' : 'Добавить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Active Windows Tab ──────────────────────────────────────────────────

interface StreamRow {
  codec: string
  gop: number
  fps: number
  resolution: string
  bitrate: number
  sourceLabel?: 'onvif' | 'rtsp' | 'probe' | 'template' | 'manual' | 'unknown'
}

interface ActiveWindowsTabProps {
  camera: Camera
  settings: { row1: any; row2: any } | null
  loading: boolean
  saving: boolean
  onSave: (row1: StreamRow, row2: StreamRow) => Promise<void>
  onPopulate: () => Promise<{ row1: StreamRow; row2: StreamRow; sourceLabel?: string; vendor?: string; model?: string } | void>
}

function ActiveWindowsTab({ camera, settings, loading, saving, onSave, onPopulate }: ActiveWindowsTabProps) {
  const defaultRow: StreamRow = { codec: 'H.264', gop: 30, fps: camera.fps || 25, resolution: '1920x1080', bitrate: 4096, sourceLabel: 'manual' }

  const [row1, setRow1] = useState<StreamRow>(settings?.row1 || defaultRow)
  const [row2, setRow2] = useState<StreamRow>(settings?.row2 || { ...defaultRow, bitrate: 2048, sourceLabel: 'manual' })

  useEffect(() => {
    if (settings) {
      setRow1({ ...settings.row1, sourceLabel: settings.row1?.sourceLabel || 'manual' })
      setRow2({ ...settings.row2, sourceLabel: settings.row2?.sourceLabel || 'manual' })
    }
  }, [settings])

  const handleSave = async () => {
    await onSave(row1, row2)
  }

  const fieldLabel = (label: string) => (
    <label className="text-kraken-muted text-[10px] mb-0.5 block uppercase tracking-wider">{label}</label>
  )

  const fieldInput = (value: any, onChange: (v: any) => void, type: string = 'text') => (
    <input
      type={type}
      value={value}
      onChange={e => onChange(type === 'number' ? (e.target.value ? parseInt(e.target.value) || 0 : 0) : e.target.value)}
      className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple font-mono"
    />
  )

  const renderRow = (row: StreamRow, setRow: (r: StreamRow) => void, label: string) => {
    const setRowWithSource = (r: StreamRow) => setRow({ ...r, sourceLabel: 'manual' })
    return (
      <div className="border border-kraken-border rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-kraken-text text-xs font-semibold">{label}</div>
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
        <div className="grid grid-cols-5 gap-3">
          <div>
            {fieldLabel('Кодек')}
            <select
              value={row.codec}
              onChange={e => setRowWithSource({ ...row, codec: e.target.value })}
              className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple"
            >
              <option value="H.264">H.264</option>
              <option value="H.265">H.265</option>
            </select>
          </div>
          <div>
            {fieldLabel('GOP')}
            {fieldInput(row.gop, v => setRowWithSource({ ...row, gop: v }), 'number')}
          </div>
          <div>
            {fieldLabel('FPS')}
            {fieldInput(row.fps, v => setRowWithSource({ ...row, fps: v }), 'number')}
          </div>
          <div>
            {fieldLabel('Разрешение')}
            <select
              value={row.resolution}
              onChange={e => setRowWithSource({ ...row, resolution: e.target.value })}
              className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-xs px-2 py-1.5 rounded-lg focus:outline-none focus:border-kraken-purple"
            >
              <option value="1920x1080">1920x1080</option>
              <option value="1280x720">1280x720</option>
              <option value="3840x2160">3840×2160 (4K)</option>
              <option value="2560x1440">2560×1440 (2K)</option>
              <option value="640x480">640×480</option>
            </select>
          </div>
          <div>
            {fieldLabel('Битрейт, кбит/с')}
            {fieldInput(row.bitrate, v => setRowWithSource({ ...row, bitrate: v }), 'number')}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-kraken-muted text-xs">Параметры активных окон для камеры</span>
        <button
          onClick={onPopulate}
          className="text-xs bg-kraken-purple/10 hover:bg-kraken-purple/20 text-kraken-purple px-3 py-1.5 rounded-lg transition-colors"
        >
          Заполнить из камеры
        </button>
      </div>

      {loading ? (
        <div className="text-center py-4 text-kraken-disabled text-sm">Загрузка настроек...</div>
      ) : (
      <>
        {renderRow(row1, setRow1, 'Строка 1 — Основной поток')}
        {renderRow(row2, setRow2, 'Строка 2 — Дополнительный поток')}

          <div className="flex gap-3 mt-2">
            <button onClick={handleSave} disabled={saving} className="btn-primary flex-1">
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

