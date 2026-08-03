"""
AIManager - Единая точка входа для AI операций

Весь остальной проект должен работать только через AIManager.
Не знает, какой Router используется внутри.
"""

from ..detectors.scrfd import SCRFD
from ..recognizers.arcface import ArcFace
from ..database.faiss import FAISS
from ..router.detector_router import DetectorRouter
from ..router.recognizer_router import RecognizerRouter
from ..router.tracker_router import TrackerRouter
from ..utils.image_quality import ImageQuality


class AIManager:
    """
    Единый менеджер AI операций.
    
    Скрывает детали реализации (рouters, конкретные модели) от остальной системы.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.detector_router = DetectorRouter(self.config.get('router', {}))
        self.recognizer_router = RecognizerRouter(self.config.get('router', {}))
        self.tracker_router = TrackerRouter(self.config.get('router', {}))
        self.quality_checker = ImageQuality()
        
        # Активные модули
        self.active_detector = None
        self.active_recognizer = None
        self.active_tracker = None
        
        # Кэш для оптимизации
        self._embeddings_cache = {}

    async def initialize(self) -> bool:
        """Инициализация AIManager"""
        # Загружаем активные модули
        self.active_detector = self.detector_router.get()
        self.active_recognizer = self.recognizer_router.get()
        # self.active_tracker = self.tracker_router.get()  # пока не используется
        
        # Инициализируем модули
        if self.active_detector:
            await self.active_detector.initialize()
        if self.active_recognizer:
            await self.active_recognizer.initialize()
        # if self.active_tracker:
        #     await self.active_tracker.initialize()
            
        return True

    async def detect(self, image_bytes: bytes) -> list:
        """
        Детектировать лица на изображении
        
        Args:
            image_bytes: Байты изображения
            
        Returns:
            Список детектированных лиц с координатами и эмбеддингами
        """
        # TODO: Проверить качество изображения
        # if not self.quality_checker.check(image_bytes):
        #     return []
            
        detector = self.detector_router.get()
        return await detector.detect_with_embedding(image_bytes)

    async def recognize(self, face_image: bytes, category: str = None) -> dict:
        """
        Распознать лицо
        
        Args:
            face_image: Байты изображения лица
            category: Категория для поиска (опционально)
            
        Returns:
            Результат распознавания с similarity и person_id
        """
        # Извлечь эмбеддинг
        recognizer = self.recognizer_router.get()
        embedding = await recognizer.extract_embedding(face_image)
        
        if not embedding:
            return {'error': 'Failed to extract embedding'}
            
        # Поиск в FAISS
        faiss = FAISS()
        await faiss.initialize()
        results = await faiss.search(embedding, top_k=5)
        
        return {
            'embedding': embedding,
            'matches': results
        }

    async def search(self, embedding: list, category: str = None) -> list:
        """
        Поиск по эмбеддингу в базе
        
        Args:
            embedding: Вектор эмбеддинга
            category: Категория для поиска (опционально)
            
        Returns:
            Список совпадений
        """
        faiss = FAISS()
        await faiss.initialize()
        return await faiss.search(embedding, top_k=5, threshold=0.4)

    async def track(self, frames: list) -> list:
        """
        Отследить лица по кадрам
        
        Args:
            frames: Список кадров (байты)
            
        Returns:
            Список треков с track_id
        """
        # TODO: Реализовать трекинг через TrackerRouter
        tracker = self.tracker_router.get()
        # return await tracker.track(frames)
        return []

    def get_status(self) -> dict:
        """
        Получить статус AI системы
        
        Returns:
            Словарь со статусом всех компонентов
        """
        status = {
            'cuda': True,  # Проверять через Python-сервер
            'gpu': True,   # Проверять через Python-сервер
            'components': {
                'scrfd': self.active_detector is not None and 'SCRFD' in str(type(self.active_detector)),
                'arcface': self.active_recognizer is not None and 'ArcFace' in str(type(self.active_recognizer)),
                'faiss': True,  # База всегда активна
                'bytetrack': False,
                'yoloface': False,
                'retinaface': False
            }
        }
        return status
