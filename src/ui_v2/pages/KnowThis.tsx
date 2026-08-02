export default function KnowThis() {
  return (
    <div className="space-y-6 text-kraken-text text-sm">

      <h1 className="text-xl font-bold">Что нужно знать</h1>

      <div className="space-y-4">
        <div className="bg-kraken-base rounded-lg p-4 border-l-4 border-kraken-purple">
          <div className="text-kraken-text font-bold text-sm mb-2">Особенности ИИ</div>
          <p className="text-xs text-kraken-muted leading-relaxed">
            Система использует вероятностные модели. Это означает, что распознавание не является 100% точным и зависит от множества факторов: ракурса, освещения, качества фото и даже макияжа. Для критически важных зон всегда рекомендуется использовать подтверждение оператором.
          </p>
        </div>

        <div className="bg-kraken-base rounded-lg p-4 border-l-4 border-kraken-blue">
          <div className="text-kraken-text font-bold text-sm mb-2">Приватность и данные</div>
          <p className="text-xs text-kraken-muted leading-relaxed">
            Все биометрические данные (эмбеддинги) хранятся локально в зашифрованном виде. Оригиналы фотографий также не покидают сервер. Вы несете ответственность за соблюдение местного законодательства (например, ФЗ-152 или GDPR) при использовании систем видеонаблюдения.
          </p>
        </div>

        <div className="bg-kraken-base rounded-lg p-4 border-l-4 border-kraken-green">
          <div className="text-kraken-text font-bold text-sm mb-2">Стабильность работы</div>
          <p className="text-xs text-kraken-muted leading-relaxed">
            Система Kraken спроектирована для работы 24/7. Встроены механизмы автоматического перезапуска при падении, очистки старых логов и записей. Рекомендуется использовать ИБП (источник бесперывного питания) для сервера и камер.
          </p>
        </div>
      </div>

    </div>
  )
}
