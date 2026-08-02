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

export default function Cameras() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Требования к видеокамерам</h1>

      <div className="space-y-0">
        <Req label="Разрешение"       min="640×480 (VGA)"                 rec="1920×1080 (Full HD) или 1280×720 (HD)" />
        <Req label="Частота кадров"   min="10 FPS"                        rec="25–30 FPS" />
        <Req label="Размер лица"      min="50×50 пикселей в кадре"        rec="100×100 пикселей и более" />
        <Req label="Тип подключения"  min="USB UVC или RTSP"              rec="RTSP H.264 (IP-камера)" />
        <Req label="Высота установки" min="1.8–3.0 м от пола"             rec="2.0–2.5 м от пола" />
        <Req label="Угол наклона"     min="0–30° вниз"                    rec="10–20° вниз" />
        <Req label="Расстояние"       min="0.5–6 м до лица"               rec="1.5–2.5 м до лица" />
        <Req label="Ночное видение"   min="Не обязательно"                rec="ИК-подсветка или WDR матрица" />
      </div>

      <div className="space-y-1">
        <Good>RTSP H.264 IP-камеры — самый стабильный поток, минимальная нагрузка</Good>
        <Good>RTSP H.265 — поддерживается, но требует больше ресурсов CPU для декодирования</Good>
        <Good>USB камеры — простое подключение, подходит для входных групп</Good>
        <Good>WDR (Wide Dynamic Range) — критически важно при работе против света</Good>
        <Warn>Широкоугольные объективы (fisheye) — лица по краям искажены, точность ниже</Warn>
        <Warn>Камера направлена против источника света — лицо в тени, детекция хуже</Warn>
        <Bad>Разрешение ниже 320×240 — лица не детектируются надёжно</Bad>
        <Bad>Менее 5 FPS — система пропускает людей при быстром движении</Bad>
      </div>

      <div className="bg-kraken-base rounded-lg p-3">
        <div className="text-kraken-muted text-xs font-semibold mb-2">Для ночных клубов / тёмных помещений</div>
        <Good>ИК-подсветка или встроенная LED подсветка</Good>
        <Good>Чувствительность матрицы ≤ 0.01 lux (Sony Starvis и аналоги)</Good>
        <Good>WDR для работы при цветном освещении (прожекторы, лазеры)</Good>
        <Note>Рекомендуется не более 8–16 камер на один ПК. RTSP H.264 и гигабитная сеть обязательны при 4+ потоках.</Note>
      </div>

    </div>
  )
}
