import { useState, useEffect } from 'react'
import { X, ArrowRight, Clock, User } from 'lucide-react'
import type { PersonCategory } from '../types'
import { apiFetch } from '../api/client'

interface CategoryChangeModalProps {
  personId: number
  currentCategory: string
  onClose: () => void
  onSaved: () => void
}

interface HistoryEntry {
  id: number
  old_code: string | null
  new_code: string
  reason: string | null
  changed_by: string
  created_at: string
}

export default function CategoryChangeModal({ personId, currentCategory, onClose, onSaved }: CategoryChangeModalProps) {
  const [categories, setCategories] = useState<PersonCategory[]>([])
  const [selectedCategory, setSelectedCategory] = useState(currentCategory)
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    apiFetch<PersonCategory[]>('/categories/')
      .then(setCategories)
      .catch(() => {})
    apiFetch<HistoryEntry[]>(`/persons/${personId}/category_history/`)
      .then(setHistory)
      .catch(() => {})
  }, [personId])

  const handleSave = async () => {
    if (selectedCategory === currentCategory) {
      setError('Категория не изменена')
      return
    }
    setSaving(true)
    setError('')
    try {
      await apiFetch(`/persons/${personId}/category/`, {
        method: 'POST',
        body: JSON.stringify({ category: selectedCategory, reason: reason || undefined }),
      })
      onSaved()
      onClose()
    } catch (e: any) {
      setError(e.message || 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const otherCategories = categories.filter(c => c.code !== currentCategory)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="panel p-5 w-full max-w-md mx-4 animate-fade-in" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-kraken-text font-bold text-base">Сменить категорию</h2>
            <p className="text-kraken-muted text-xs mt-0.5">Персона #{personId}</p>
          </div>
          <button onClick={onClose} className="text-kraken-muted hover:text-kraken-text">
            <X size={18} />
          </button>
        </div>

        {/* Current category */}
        <div className="mb-4 p-3 rounded-lg bg-kraken-hover border border-kraken-border">
          <div className="text-kraken-disabled text-[10px] uppercase tracking-wider mb-1">Текущая категория</div>
          <div className="text-kraken-text text-sm font-semibold">
            {categories.find(c => c.code === currentCategory)?.label || currentCategory}
          </div>
        </div>

        {/* New category selector */}
        <div className="mb-4">
          <label className="text-kraken-disabled text-[10px] uppercase tracking-wider mb-2 block">Новая категория</label>
          <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto">
            {otherCategories.map(c => (
              <button
                key={c.code}
                onClick={() => setSelectedCategory(c.code)}
                className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all text-left ${
                  selectedCategory === c.code
                    ? 'border-kraken-purple bg-kraken-purple/10'
                    : 'border-kraken-border hover:border-kraken-border-hover'
                }`}
              >
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: c.color }}
                />
                <span className={`text-sm ${selectedCategory === c.code ? 'text-kraken-text font-semibold' : 'text-kraken-muted'}`}>
                  {c.label}
                </span>
                {selectedCategory === c.code && <ArrowRight size={14} className="ml-auto text-kraken-purple" />}
              </button>
            ))}
          </div>
        </div>

        {/* Reason */}
        <div className="mb-4">
          <label className="text-kraken-disabled text-[10px] uppercase tracking-wider mb-1 block">Причина смены категории</label>
          <select
            value={reason}
            onChange={e => setReason(e.target.value)}
            className="w-full bg-kraken-hover border border-kraken-border text-kraken-text text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-kraken-purple"
          >
            <option value="">Выберите причину...</option>
            <option value="Зачинщик / агрессор">Зачинщик / агрессор</option>
            <option value="Соучастник ЧП">Соучастник ЧП</option>
            <option value="Нарушитель">Нарушитель</option>
            <option value="Ошибка классификации">Ошибка классификации</option>
            <option value="По решению руководства">По решению руководства</option>
            <option value="Другое">Другое</option>
          </select>
        </div>

        {error && <div className="text-kraken-red text-xs mb-3">{error}</div>}

        {/* History */}
        {history.length > 0 && (
          <div className="mb-4">
            <div className="text-kraken-disabled text-[10px] uppercase tracking-wider mb-2 flex items-center gap-1">
              <Clock size={10} /> История изменений
            </div>
            <div className="flex flex-col gap-1.5 max-h-32 overflow-y-auto">
              {history.map((h, i) => (
                <div key={h.id} className="flex items-center gap-2 text-xs p-2 rounded bg-kraken-hover/50">
                  <span className="text-kraken-muted">{h.old_code || '—'}</span>
                  <ArrowRight size={10} className="text-kraken-purple" />
                  <span className="text-kraken-text font-medium">{h.new_code}</span>
                  {h.reason && <span className="text-kraken-disabled truncate">· {h.reason}</span>}
                  <span className="text-kraken-disabled ml-auto whitespace-nowrap">
                    {new Date(h.created_at).toLocaleDateString('ru-RU')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <button onClick={onClose} className="btn-ghost flex-1 text-sm">Отмена</button>
          <button onClick={handleSave} disabled={saving || selectedCategory === currentCategory} className="btn-primary flex-1 text-sm disabled:opacity-50">
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  )
}
