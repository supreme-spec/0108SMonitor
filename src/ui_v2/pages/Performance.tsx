import { CheckCircle, AlertTriangle, Info, HardDrive } from 'lucide-react'

interface ReqProps {
  label: string
  min: string
  rec?: string
}

function Req({ label, min, rec }: ReqProps) {
  return (
    <div className="py-4 border-b border-kraken-border last:border-0 min-w-0">
      <h3 className="text-kraken-muted text-xs uppercase tracking-wide font-bold border-l-2 border-kraken-purple pl-2 mb-3">
        {label}
      </h3>
      <div className="kraken-req-group">
        <div className="kraken-req-line">
          <span className="kraken-req-tag kraken-req-tag--min">Минимум</span>
          <span className="kraken-req-value kraken-req-value--min">{min}</span>
        </div>
        {rec ? (
          <div className="kraken-req-line">
            <span className="kraken-req-tag kraken-req-tag--rec">Рекомендуется</span>
            <span className="kraken-req-value kraken-req-value--rec">{rec}</span>
          </div>
        ) : null}
      </div>
    </div>
  )
}

function Good({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 py-1">
      <CheckCircle size={14} className="text-kraken-green flex-shrink-0 mt-0.5" />
      <span className="text-kraken-text text-sm">{children}</span>
    </div>
  )
}

function Warn({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 py-1">
      <AlertTriangle size={14} className="text-yellow-400 flex-shrink-0 mt-0.5" />
      <span className="text-kraken-muted text-sm">{children}</span>
    </div>
  )
}

function Note({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 py-1">
      <Info size={14} className="text-kraken-blue flex-shrink-0 mt-0.5" />
      <span className="text-kraken-muted text-sm">{children}</span>
    </div>
  )
}

interface ScaleRowProps {
  cameras: string
  workers: string
  note: string
}

function ScaleRow({ cameras, workers, note }: ScaleRowProps) {
  return (
    <div className="py-2.5 border-b border-kraken-border last:border-0 text-xs min-w-0 sm:grid sm:grid-cols-[5rem_4rem_minmax(0,1fr)] sm:gap-x-4 sm:items-start">
      <span className="text-kraken-purple font-bold block mb-0.5 sm:mb-0">{cameras}</span>
      <span className="text-kraken-text font-mono block mb-0.5 sm:mb-0">{workers}</span>
      <span className="text-kraken-muted leading-relaxed break-words block">{note}</span>
    </div>
  )
}

export default function Performance() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Производительность и масштабируемость</h1>

      <div className="space-y-0">
        <Req label="Камеры"              min="1 камера"                   rec="До 100 000 эмбеддингов (FAISS)" />
        <Req label="База лиц"            min="1 человек"                  rec="До 100 000 эмбеддингов (FAISS)" />
        <Req label="AI воркеры"          min="1 воркер"                   rec="до 4 (NVIDIA) / до 2 (AMD DirectML)" />
        <Req label="Задержка AI"         min="~0.8–1.4 с на кадр (CPU)"    rec="~0.03–0.08 с (CUDA, 1 лицо)" />
        <Req label="Частота AI"          min="Каждый 20-й кадр (~2.5/с)"  rec="AI_FRAME_EVERY=20 при 30 FPS" />
        <Req label="Хранение записей"    min="Авто-удаление через 90 дней" rec="Настраивается вручную" />
      </div>

      <div className="bg-kraken-base rounded-lg p-3 border border-kraken-border">
        <div className="text-kraken-disabled text-[10px] uppercase tracking-widest mb-2">
          Масштабирование AI-пула (автоматически)
        </div>
        <div className="hidden sm:grid sm:grid-cols-[5rem_4rem_minmax(0,1fr)] gap-x-3 text-[10px] text-kraken-disabled uppercase mb-1">
          <span>Камер</span>
          <span>Воркеров</span>
          <span>Примечание</span>
        </div>
        <ScaleRow cameras="1" workers="1" note="Минимальная нагрузка" />
        <ScaleRow cameras="2–4" workers="2" note="Типичный офис / вход" />
        <ScaleRow cameras="5–8" workers="3" note="Средний объект" />
        <ScaleRow cameras="9–16" workers="4*" note="* макс. 2 воркера на AMD/Intel DirectML; выше 16 камер — несколько серверов Kraken" />
      </div>

      <div className="space-y-1">
        <Good>FAISS IndexFlatIP — точный поиск, масштабируется до 100 000+ эмбеддингов</Good>
        <Good>Thread-local ONNX — отдельная сессия на каждый AI-воркер</Good>
        <Good>RLock на FAISS — параллельное чтение из нескольких воркеров</Good>
        <Warn>Более 16 камер на один ПК — растёт очередь AI и задержка; несколько серверов или снижение разрешения / AI_FRAME_EVERY</Warn>
        <Note>Видеозаписи: ~1–3 GB в сутки на камеру (зависит от активности)</Note>
        <Note>PostgreSQL: только localhost (порт 5433)</Note>
      </div>

    </div>
  )
}
