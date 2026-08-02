import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'

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

function Bad({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 py-1">
      <XCircle size={14} className="text-kraken-red flex-shrink-0 mt-0.5" />
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

export default function Lighting() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Требования к освещению</h1>

      <div className="space-y-0">
        <Req label="Освещённость лица"  min="≥ 50 lux (тусклый свет)"    rec="200–500 lux (равномерное)" />
        <Req label="Направление света"  min="Любое (не строго сзади)"     rec="Фронтальное или 45° сбоку" />
        <Req label="Цветовая температура" min="Любая"                     rec="Нейтральная (система работает в YCrCb)" />
        <Req label="Тени на лице"        min="До 40% площади лица"        rec="Минимальные тени" />
      </div>

      <div className="space-y-1">
        <Good>Цветное освещение (RGB прожекторы) — CLAHE нормализует контраст автоматически</Good>
        <Good>Смешанное освещение — система адаптируется через YCrCb преобразование</Good>
        <Warn>Мигающий стробоскоп — снижает качество кадров, возможны пропуски</Warn>
        <Warn>Яркие пятна на лице (прожектор в упор) — пересвет снижает точность</Warn>
        <Bad>Освещение строго сзади (силуэт) — лицо не детектируется</Bad>
        <Bad>Полная темнота без ИК — детекция невозможна</Bad>
      </div>

      <div className="bg-kraken-base rounded-lg p-3">
        <div className="text-kraken-muted text-xs font-semibold mb-2">Встроенная компенсация (CLAHE)</div>
        <Note>Видеопоток: мягкая нормализация (clipLimit=1.5) — только на кропе лица</Note>
        <Note>Фотографии: более агрессивная (clipLimit=2.0) — для архивных и тёмных фото</Note>
        <Note>Обрабатывается только область лица, не весь кадр — быстро и без артефактов</Note>
      </div>

    </div>
  )
}
