import { CheckCircle, Info } from 'lucide-react'

interface TechRowProps {
  name: string
  version: string
  desc: string
}

function TechRow({ name, version, desc }: TechRowProps) {
  return (
    <div className="py-2.5 border-b border-kraken-border last:border-0 space-y-1 min-w-0">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
        <span className="text-kraken-text text-sm font-mono break-all">{name}</span>
        <span className="text-kraken-purple text-xs font-bold shrink-0">{version}</span>
      </div>
      <p className="text-kraken-muted text-xs leading-relaxed break-words">{desc}</p>
    </div>
  )
}

export default function TechStack() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Технологический стек</h1>

      {/* ── System core ── */}
      <div className="mb-6 bg-kraken-base rounded-lg p-4 border-l-4 border-kraken-purple">
        <div className="text-kraken-text font-bold text-sm mb-2">Uniface 2.0 (Core AI Engine)</div>
        <p className="text-xs text-kraken-muted leading-relaxed mb-3">
          Сердцем системы является проприетарный движок <strong className="text-kraken-purple">Uniface 2.0</strong>,
          объединяющий последние достижения в области нейронных сетей для работы с лицами.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[11px]">
          <div className="space-y-2">
            <div className="text-kraken-text font-semibold uppercase tracking-wider text-[9px]">Детекция (SCRFD)</div>
            <ul className="space-y-1 text-kraken-muted">
              <li className="flex items-center gap-2"><CheckCircle size={10} className="text-kraken-green" /> Скорость: до 2мс на кадр</li>
              <li className="flex items-center gap-2"><CheckCircle size={10} className="text-kraken-green" /> Лица в масках и под углом</li>
              <li className="flex items-center gap-2"><CheckCircle size={10} className="text-kraken-green" /> Контровый и сложный свет</li>
            </ul>
          </div>
          <div className="space-y-2">
            <div className="text-kraken-text font-semibold uppercase tracking-wider text-[9px]">Распознавание (ArcFace)</div>
            <ul className="space-y-1 text-kraken-muted">
              <li className="flex items-center gap-2"><CheckCircle size={10} className="text-kraken-green" /> Точность: 99.83% на LFW</li>
              <li className="flex items-center gap-2"><CheckCircle size={10} className="text-kraken-green" /> 512-мерные эмбеддинги</li>
              <li className="flex items-center gap-2"><CheckCircle size={10} className="text-kraken-green" /> Устойчивость к возрасту</li>
            </ul>
          </div>
        </div>
      </div>

      {/* ── Backend ── */}
      <div>
        <div className="text-kraken-disabled text-[10px] uppercase tracking-widest mb-2">Backend</div>
        <TechRow name="Python"          version="3.13.6"    desc="Основной язык бэкенда" />
        <TechRow name="FastAPI"         version="0.136.0"   desc="REST API + WebSocket сервер" />
        <TechRow name="PostgreSQL"      version="16.6"      desc="База данных (portable, порт 5433)" />
        <TechRow name="SQLAlchemy"      version="2.0.41"    desc="ORM для работы с БД" />
        <TechRow name="uniface"         version="2.0.0"     desc="Детекция и распознавание лиц" />
        <TechRow name="onnxruntime"     version="1.21.0"    desc="Инференс AI моделей (CUDA/CPU)" />
        <TechRow name="faiss-cpu"       version="1.10.0"    desc="Векторный поиск по эмбеддингам" />
        <TechRow name="opencv-python"   version="4.11.0.86" desc="Захват видео, обработка кадров" />
        <TechRow name="numpy"           version="2.3.2"     desc="Матричные операции" />
      </div>

      {/* ── Frontend ── */}
      <div>
        <div className="text-kraken-disabled text-[10px] uppercase tracking-widest mb-2">Frontend</div>
        <TechRow name="React"           version="19"        desc="UI фреймворк" />
        <TechRow name="TypeScript"      version="5.8"       desc="Типизация" />
        <TechRow name="Vite"            version="6"         desc="Сборщик" />
        <TechRow name="Tailwind CSS"    version="3"         desc="Стили" />
      </div>

      {/* ── AI Models ── */}
      <div>
        <div className="text-kraken-disabled text-[10px] uppercase tracking-widest mb-2">AI Модели</div>
        <TechRow name="scrfd_10g.onnx"    version="16 MB"   desc="Детекция лиц в видеопотоке (95.16% WIDER FACE Hard)" />
        <TechRow name="scrfd_500m.onnx"   version="2.4 MB"  desc="Детекция лиц на фото (лёгкая модель)" />
        <TechRow name="arcface_resnet.onnx" version="166 MB" desc="Распознавание лиц (99.83% LFW, 97.25% IJB-C)" />
      </div>

      <div className="bg-kraken-base rounded-lg p-3">
        <div className="flex items-start gap-2">
          <Info size={14} className="text-kraken-blue flex-shrink-0 mt-0.5" />
          <span className="text-xs text-kraken-muted">
            Модели скачиваются автоматически при первом запуске в <span className="font-mono text-kraken-text">~/.uniface/models/</span>
          </span>
        </div>
      </div>

    </div>
  )
}
