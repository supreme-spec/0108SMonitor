import { Info, CheckCircle, AlertTriangle, XCircle, Zap } from 'lucide-react'

export default function Description() {
  return (
    <div className="space-y-6 text-kraken-text text-sm leading-relaxed">

      <h1 className="text-xl font-bold">Описание системы</h1>

      <p>
        <strong className="text-kraken-purple">Kraken Security System</strong> — это современная автономная система распознавания лиц,
        предназначенная для обеспечения безопасности и аналитики в режиме реального времени. Система способна обрабатывать
        множество видеопотоков одновременно, идентифицировать людей по базе лиц и мгновенно оповещать о событиях.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
        <div className="bg-kraken-hover p-3 rounded-lg">
          <div className="text-kraken-purple font-bold text-xs mb-1">Детектор SCRFD</div>
          <div className="text-xs text-kraken-muted">Использует передовой алгоритм SCRFD, который находит лица даже в масках, под углом или при плохом освещении.</div>
        </div>
        <div className="bg-kraken-hover p-3 rounded-lg">
          <div className="text-kraken-green font-bold text-xs mb-1">Скорость</div>
          <div className="text-xs text-kraken-muted">Использование FAISS и ONNX позволяет искать по базе из 100 000+ лиц за миллисекунды.</div>
        </div>
        <div className="bg-kraken-hover p-3 rounded-lg">
          <div className="text-kraken-blue font-bold text-xs mb-1">Масштабируемость</div>
          <div className="text-xs text-kraken-muted leading-relaxed">
            На одном сервере комфортно 4–8 RTSP/USB камер; до 16 — при мощном CPU и GPU. AI-нагрузка масштабируется пулом воркеров (до 4 на NVIDIA, до 2 на AMD DirectML).
          </div>
        </div>
        <div className="bg-kraken-hover p-3 rounded-lg">
          <div className="text-yellow-400 font-bold text-xs mb-1">Умная запись</div>
          <div className="text-xs text-kraken-muted">Автоматическая запись коротких роликов при обнаружении конкретных лиц.</div>
        </div>
      </div>

      <div className="mt-4 text-xs text-kraken-disabled italic p-3 bg-kraken-base rounded-lg border-l-4 border-kraken-purple">
        Оптимальный режим: детекция SCRFD на CPU (ограничение ONNX DirectML), распознавание ArcFace — CUDA (NVIDIA), DirectML (AMD/Intel) или CPU.
      </div>
    </div>
  )
}
