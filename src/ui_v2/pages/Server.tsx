import { CheckCircle, AlertTriangle, Info, Zap } from 'lucide-react'

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

export default function Server() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Требования к серверу (ПК)</h1>

      <div className="space-y-0">
        <Req label="Процессор"       min="4 ядра / 8 потоков, 2.5 GHz"   rec="8 ядер / 16 потоков (Ryzen 7 / Core i7+)" />
        <Req label="Оперативная память" min="8 GB RAM"                    rec="16 GB RAM" />
        <Req label="Диск"            min="10 GB (HDD/SSD)"                rec="100 GB+ SSD (видеоархив ~1–3 GB/день)" />
        <Req label="Видеокарта"      min="Любая (CPU режим)"              rec="NVIDIA GPU (8GB+ VRAM для 10+ камер)" />
        <Req label="ОС"              min="Windows 10 / 11 (64-bit)"       rec="Windows 11, последние обновления" />
        <Req label="Сеть"            min="100 Мбит/с LAN"                 rec="1 Гбит/с (Порты: 3000, 8001, 554)" />
      </div>

      {/* ── Network settings ── */}
      <div className="space-y-2 bg-kraken-hover/20 p-4 rounded-xl border border-kraken-border">
        <div className="flex items-center gap-2 text-kraken-purple font-bold text-xs uppercase tracking-widest mb-1">
          <Zap size={14} /> Сетевые настройки
        </div>
        <Good>Порт 3000 — Основной интерфейс и API системы.</Good>
        <Good>Порт 8001 — Python Face Engine (только localhost).</Good>
        <Good>Порт 554 — Стандартный порт RTSP для получения видеопотока.</Good>
        <Note>Для удаленного доступа пробросьте порт 3000 на роутере.</Note>
      </div>

      {/* ── GPU acceleration ── */}
      <div className="space-y-2 bg-kraken-hover/20 p-4 rounded-xl border border-kraken-border">
        <div className="flex items-center gap-2 text-kraken-purple font-bold text-xs uppercase tracking-widest mb-1">
          <Zap size={14} /> GPU Ускорение
        </div>
        <Good>NVIDIA GPU — Встроено. Программа сама установит необходимые библиотеки и пакеты.</Good>
        <Good>Гибридный режим — Детекция лиц на CPU, Распознавание на GPU. Это исключает задержки и экономит видеопамять.</Good>
        <Good>Автоматическая установка — При первом запуске подбирается onnxruntime-gpu, DirectML или CPU.</Good>
        <Note>Политика «stable» — только CPU (максимальная стабильность). «auto» — CUDA/DirectML при наличии.</Note>
        <Warn>AMD/Intel: до 2 параллельных AI-воркеров с DirectML (защита от сбоев драйвера).</Warn>
      </div>

    </div>
  )
}
