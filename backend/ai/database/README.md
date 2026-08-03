# Базы данных для поиска

Модули быстрого поиска по эмбеддингам:

- **FAISS** (активен) — быстрый поиск с IVF индексом
- **HNSW** (планируется) — граф-based поиск
- **IVF-Adam** (планируется) — адаптивный IVF

## Интерфейс BaseDatabase

- `add_embedding(embedding, person_id)` — добавить эмбеддинг
- `search(embedding, top_k, threshold)` — поиск
- `build_index()` — построить индекс
- `save(path)` — сохранить индекс
- `load(path)` — загрузить индекс
