import { Info, CheckCircle } from 'lucide-react'

interface ThreshRowProps {
  pct: string
  cosine: string
  label: string
  color: string
  note: string
}

function ThreshRow({ pct, cosine, label, color, note }: ThreshRowProps) {
  return (
    <div className="px-3 py-2.5 rounded-lg bg-kraken-hover mb-1.5 space-y-1.5 min-w-0">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className={`text-xs font-bold shrink-0 ${color}`}>{pct}</span>
        <span className="text-kraken-disabled text-xs font-mono shrink-0">{cosine}</span>
        <span className="text-kraken-disabled text-[10px] leading-snug break-words">{note}</span>
      </div>
      <p className="text-kraken-text text-xs leading-relaxed break-words">{label}</p>
    </div>
  )
}

export default function Thresholds() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Пороги распознавания</h1>

      <p className="text-kraken-muted text-sm mb-4">
        Минимальный процент совпадения для подтверждения личности.
        Настраивается в разделе <strong className="text-kraken-text">Система → Чувствительность</strong>.
      </p>

      <div className="space-y-1">
        <ThreshRow pct="0–20%"   cosine="0.28–0.39" label="Очень мягко — много ложных совпадений"          color="text-kraken-red"    note="Не рекомендуется" />
        <ThreshRow pct="20–30%"  cosine="0.39–0.45" label="Мягко — плохое освещение, старые фото"           color="text-yellow-400"    note="Осторожно" />
        <ThreshRow pct="30–50%"  cosine="0.45–0.57" label="Оптимально — ночной клуб, стандарт"              color="text-kraken-green"  note="✓ Рекомендуется" />
        <ThreshRow pct="50–65%"  cosine="0.57–0.65" label="Строго — хорошее освещение, качественные фото"   color="text-kraken-blue"   note="Меньше ложных" />
        <ThreshRow pct="65–100%" cosine="0.65–0.85" label="Максимальная точность — идеальные условия"        color="text-kraken-purple" note="Много пропусков" />
      </div>

      <div className="space-y-1 mt-4">
        <div className="flex items-start gap-2 py-1">
          <Info size={14} className="text-kraken-blue flex-shrink-0 mt-0.5" />
          <span className="text-sm text-kraken-muted">
            BLACKLIST категория: порог автоматически снижается на 8% для быстрого срабатывания
          </span>
        </div>
        <div className="flex items-start gap-2 py-1">
          <Info size={14} className="text-kraken-blue flex-shrink-0 mt-0.5" />
          <span className="text-sm text-kraken-muted">
            Подтверждение: 3 последовательных кадра перед созданием события (защита от ложных)
          </span>
        </div>
        <div className="flex items-start gap-2 py-1">
          <Info size={14} className="text-kraken-blue flex-shrink-0 mt-0.5" />
          <span className="text-sm text-kraken-muted">
            Cooldown: 30 секунд между событиями одного человека
          </span>
        </div>
      </div>

    </div>
  )
}
