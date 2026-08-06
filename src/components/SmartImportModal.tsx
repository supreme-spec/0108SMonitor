import { useState, useRef } from 'react'
import { X, Upload, FileText, Users, AlertTriangle } from 'lucide-react'

interface SmartImportModalProps {
  onClose: () => void
  onDone: () => void
}

interface ImportResult {
  total: number
  created: number
  updated: number
  skipped: number
  errors: string[]
}

export default function SmartImportModal({ onClose, onDone }: SmartImportModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string[]>([])
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState('')
  const [mode, setMode] = useState<'create' | 'update'>('create')
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setResult(null)
    setError('')

    const reader = new FileReader()
    reader.onload = (ev) => {
      const text = ev.target?.result as string
      const lines = text.split('\n').filter(l => l.trim())
      setPreview(lines.slice(0, 5))
    }
    reader.readAsText(f)
  }

  const handleImport = async () => {
    if (!file) return
    setImporting(true)
    setError('')
    setResult(null)

    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('mode', mode)

      const res = await fetch('/api/persons/smart_import', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('kraken_token') || ''}`,
        },
        body: fd,
      })

      if (!res.ok) {
        const text = await res.text()
        try { throw new Error(JSON.parse(text).detail || `Ошибка ${res.status}`) }
        catch { throw new Error(`Ошибка сервера ${res.status}`) }
      }

      const data = await res.json()
      setResult(data)
    } catch (e: any) {
      setError(e.message || 'Ошибка импорта')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={onClose}>
      <div className="panel p-5 w-full max-w-lg mx-4 animate-fade-in" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-kraken-text font-bold text-base">Умный импорт персонала</h2>
            <p className="text-kraken-muted text-xs mt-0.5">Загрузка из CSV/Excel с автопоиском дубликатов</p>
          </div>
          <button onClick={onClose} className="text-kraken-muted hover:text-kraken-text">
            <X size={18} />
          </button>
        </div>

        {!result ? (
          <>
            {/* Mode selector */}
            <div className="mb-4">
              <label className="text-kraken-disabled text-[10px] uppercase tracking-wider mb-2 block">Режим импорта</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setMode('create')}
                  className={`flex-1 py-2 rounded-lg text-xs font-semibold border transition-colors ${
                    mode === 'create'
                      ? 'bg-kraken-purple/20 border-kraken-purple text-kraken-purple'
                      : 'bg-kraken-hover border-kraken-border text-kraken-muted hover:text-kraken-text'
                  }`}
                >
                  <Users size={13} className="inline mr-1" />
                  Только новых
                </button>
                <button
                  onClick={() => setMode('update')}
                  className={`flex-1 py-2 rounded-lg text-xs font-semibold border transition-colors ${
                    mode === 'update'
                      ? 'bg-kraken-purple/20 border-kraken-purple text-kraken-purple'
                      : 'bg-kraken-hover border-kraken-border text-kraken-muted hover:text-kraken-text'
                  }`}
                >
                  <FileText size={13} className="inline mr-1" />
                  Обновлять существующих
                </button>
              </div>
            </div>

            {/* File upload */}
            <div className="mb-4">
              <label className="w-full border-2 border-dashed border-kraken-border hover:border-kraken-purple rounded-xl py-6 flex flex-col items-center gap-2 transition-colors cursor-pointer block">
                <Upload size={24} className="text-kraken-muted" />
                <span className="text-kraken-muted text-sm">
                  {file ? file.name : 'Нажмите для выбора файла'}
                </span>
                <span className="text-kraken-disabled text-xs">CSV, XLS, XLSX</span>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv,.xls,.xlsx"
                  className="hidden"
                  onChange={handleFile}
                />
              </label>

              {preview.length > 0 && (
                <div className="mt-2 p-2 bg-kraken-hover rounded-lg">
                  <div className="text-kraken-disabled text-[10px] uppercase tracking-wider mb-1">Первые строки:</div>
                  {preview.map((line, i) => (
                    <div key={i} className="text-kraken-muted text-[11px] font-mono truncate">
                      {line}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {error && <div className="text-kraken-red text-xs mb-3">{error}</div>}

            <div className="flex gap-2">
              <button onClick={onClose} className="btn-ghost flex-1 text-sm">Отмена</button>
              <button onClick={handleImport} disabled={!file || importing} className="btn-primary flex-1 text-sm disabled:opacity-50">
                {importing ? 'Импорт...' : 'Импортировать'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="text-center py-4">
              <div className="text-3xl mb-2">✅</div>
              <div className="text-kraken-text font-bold text-sm">Импорт завершён</div>
              <div className="text-kraken-muted text-xs mt-1">
                Создано: <span className="text-kraken-green font-bold">{result.created}</span> · 
                Обновлено: <span className="text-kraken-blue font-bold">{result.updated}</span> · 
                Пропущено: <span className="text-kraken-muted">{result.skipped}</span>
              </div>
              {result.errors.length > 0 && (
                <div className="mt-3 text-left">
                  <div className="text-kraken-red text-xs font-semibold mb-1 flex items-center gap-1">
                    <AlertTriangle size={12} /> Ошибки:
                  </div>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {result.errors.slice(0, 10).map((err, i) => (
                      <div key={i} className="text-kraken-red text-[11px]">{err}</div>
                    ))}
                    {result.errors.length > 10 && (
                      <div className="text-kraken-disabled text-[10px]">...и ещё {result.errors.length - 10}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
            <button onClick={onDone} className="btn-primary w-full mt-4 text-sm">Готово</button>
          </>
        )}
      </div>
    </div>
  )
}
