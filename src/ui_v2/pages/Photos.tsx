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

export default function Photos() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Требования к фотографиям для базы лиц</h1>

      <div className="space-y-0">
        <Req label="Формат"           min="JPEG, PNG, BMP, WEBP"         rec="JPEG (качество ≥ 85%)" />
        <Req label="Разрешение"       min="100×100 пикселей (лицо)"      rec="400×400 пикселей и выше" />
        <Req label="Лицо в кадре"     min="≥ 30% площади фото"           rec="≥ 50% площади, фронтальный ракурс" />
        <Req label="Поворот головы"   min="До 45° от фронтального"       rec="До 20° (почти прямо в камеру)" />
        <Req label="Фокус"            min="Допускается лёгкое размытие"  rec="Чёткое изображение" />
        <Req label="Количество фото"  min="1 фото на человека"           rec="3–5 фото (разные ракурсы и освещение)" />
      </div>

      <div className="space-y-1">
        <Good>Фото с живой камеры — лучший вариант, условия совпадают с реальным использованием</Good>
        <Good>Несколько фото с разным освещением — значительно повышает точность</Good>
        <Good>Система автоматически накапливает снимки с камер (до 10 фото на человека)</Good>
        <Warn>Профильное фото (поворот &gt; 45°) — эмбеддинг менее точный</Warn>
        <Warn>Очень маленькое лицо (&lt; 50×50 px) — детектор может не найти</Warn>
        <Bad>Лицо перекрыто маской, рукой, волосами — эмбеддинг не извлекается</Bad>
        <Bad>Сильный пересвет или недосвет — детекция не срабатывает</Bad>
      </div>

      <div className="bg-kraken-base rounded-lg p-3">
        <div className="text-kraken-muted text-xs font-semibold mb-2">Автоматическая обработка при загрузке</div>
        <div className="space-y-1 text-xs text-kraken-muted">
          <div className="flex items-center gap-2"><span className="text-kraken-purple font-bold">1</span> Детекция лица (SCRFD_500M)</div>
          <div className="flex items-center gap-2"><span className="text-kraken-purple font-bold">2</span> Вырезание с паддингом 40% (захват лба и подбородка)</div>
          <div className="flex items-center gap-2"><span className="text-kraken-purple font-bold">3</span> Апскейл до минимум 256×256 если лицо маленькое</div>
          <div className="flex items-center gap-2"><span className="text-kraken-purple font-bold">4</span> CLAHE нормализация освещения</div>
          <div className="flex items-center gap-2"><span className="text-kraken-purple font-bold">5</span> Face alignment по 5 ключевым точкам</div>
          <div className="flex items-center gap-2"><span className="text-kraken-purple font-bold">6</span> Генерация ~12 аугментированных эмбеддингов</div>
        </div>
      </div>

    </div>
  )
}
