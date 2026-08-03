"""
FAISS - текущая база данных для поиска
"""

from ..base import BaseModule, ModuleType, ModuleStatus, ModuleInfo
from typing import List, Dict


class FAISS(BaseModule):
    """
    FAISS (Facebook AI Similarity Search) - база для быстрого поиска
    
    Используется для поиска по эмбеддингам в базе лиц.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.info = ModuleInfo(
            name="FAISS",
            type=ModuleType.DATABASE,
            version="4.7.4",
            provider="CUDA",
            enabled=True,
            status=ModuleStatus.ACTIVE,
            description="Быстрый поиск по эмбеддингам с IVF индексом",
            priority=1,
            gpu_required=True
        )
        self.index = None
        self.persons = []
        self.embedding_to_person = {}

    async def initialize(self) -> bool:
        """Инициализация FAISS"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def load_models(self) -> bool:
        """Загрузка FAISS индекса"""
        self.status = ModuleStatus.ACTIVE
        return True

    async def unload_models(self) -> bool:
        """Выгрузка FAISS индекса"""
        self.status = ModuleStatus.INSTALLED
        return True

    async def add_embedding(self, embedding: List[float], person_id: int, person_name: str):
        """Добавить эмбеддинг в индекс"""
        # TODO: Реализовать добавление в FAISS
        pass

    async def search(self, embedding: List[float], top_k: int = 5, threshold: float = 0.4) -> List[Dict]:
        """Поиск по эмбеддингам"""
        # TODO: Реализовать поиск в FAISS
        return []
