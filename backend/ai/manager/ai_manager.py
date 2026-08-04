"""
AIManager - Единая точка входа для AI операций

Весь остальной проект должен работать только через AIManager.
Не знает, какой Router используется внутри.
"""

import os
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from ..detectors.scrfd import SCRFD
from ..detectors.yoloface import YOLOFace
from ..detectors.retinaface import RetinaFace
from ..recognizers.arcface import ArcFace
from ..trackers.bytetrack import ByteTrack
from ..database.faiss import FAISS
from ..router.detector_router import DetectorRouter
from ..router.recognizer_router import RecognizerRouter
from ..router.tracker_router import TrackerRouter
from ..base import ModuleStatus, ModuleInfo


class AIManager:
    """
    Единый менеджер AI операций.
    
    Скрывает детали реализации (рouters, конкретные модели) от остальной системы.
    Поддерживает динамическое переключение модулей без перезапуска.
    """

    CONFIG_PATH = Path(__file__).parent.parent.parent / "ai_config.json"
    _instance = None
    
    @staticmethod
    def get_instance() -> 'AIManager':
        """Get singleton instance."""
        return AIManager()
    
    def __new__(cls, config: dict = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: dict = None):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"AIManager.__init__ called, self._initialized={getattr(self, '_initialized', 'N/A')}")
        
        if self._initialized:
            logger.info("AIManager already initialized, skipping")
            return
        self.config = config or {}
        self._config_data = self._load_config()
        
        # Router instances
        self.detector_router = DetectorRouter(self._config_data.get('router', {}))
        self.recognizer_router = RecognizerRouter(self._config_data.get('router', {}))
        self.tracker_router = TrackerRouter(self._config_data.get('router', {}))
        
        # Active modules cache
        self._active_detector: Optional[Any] = None
        self._active_recognizer: Optional[Any] = None
        self._active_tracker: Optional[Any] = None
        self._faiss: Optional[FAISS] = None
        
        # Module classes mapping
        self._detector_classes = {
            'scrfd': SCRFD,
            'yoloface': YOLOFace,
            'retinaface': RetinaFace,
        }
        self._recognizer_classes = {
            'arcface': ArcFace,
            'adaface': ArcFace,  # AdaFace пока использует ту же реализацию
        }
        self._tracker_classes = {
            'bytetrack': ByteTrack,
            'botsort': ByteTrack,  # BoT-SORT пока использует ту же реализацию
        }
        
        self._initialized = True

    def _load_config(self) -> dict:
        """Загрузить конфигурацию из ai_config.json"""
        try:
            if self.CONFIG_PATH.exists():
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load ai_config.json: {e}")
        return {
            "active": {
                "detector": "scrfd",
                "recognizer": "arcface",
                "tracker": "none"
            },
            "detectors": {"scrfd": {"enabled": True}},
            "recognizers": {"arcface": {"enabled": True}},
            "trackers": {}
        }

    def _save_config(self) -> bool:
        """Сохранить конфигурацию в ai_config.json"""
        try:
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save ai_config.json: {e}")
            return False

    async def initialize(self) -> bool:
        """Инициализация AIManager и загрузка активных модулей"""
        # Загружаем конфигурацию
        self._config_data = self._load_config()
        
        # Загружаем активные модули
        active_detector = self._config_data.get('active', {}).get('detector', 'scrfd')
        active_recognizer = self._config_data.get('active', {}).get('recognizer', 'arcface')
        
        await self._load_detector(active_detector)
        await self._load_recognizer(active_recognizer)
        
        return True

    async def _load_detector(self, name: str) -> bool:
        """Загрузить детектор по имени"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"_load_detector called: {name}")
        
        try:
            if name == 'none':
                self._active_detector = None
                self.detector_router._current_detector = None
                return True
            
            if name not in self._detector_classes:
                print(f"Unknown detector: {name}")
                logger.error(f"Unknown detector: {name}")
                return False
            
            logger.info(f"Unloading old detector: {self._active_detector}")
            
            # Выгружаем старый модуль
            if self._active_detector:
                await self._active_detector.unload_models()
            
            logger.info(f"Creating new detector instance: {name}")
            
            # Создаем новый экземпляр
            detector_class = self._detector_classes[name]
            self._active_detector = detector_class()
            
            logger.info(f"Initializing detector: {name}")
            
            await self._active_detector.initialize()
            
            # Обновляем router
            self.detector_router._current_detector = self._active_detector
            
            # Обновляем статус в конфиге
            self._config_data['active']['detector'] = name
            if name in self._config_data.get('detectors', {}):
                self._config_data['detectors'][name]['status'] = 'active'
            
            self._save_config()
            
            logger.info(f"Loaded detector: {name}")
            return True
            
        except Exception as e:
            print(f"Failed to load detector {name}: {e}")
            import traceback as tb
            logger.error(f"Failed to load detector {name}: {e}")
            logger.error(tb.format_exc())
            return False

    async def _load_recognizer(self, name: str) -> bool:
        """Загрузить рекогнайзер по имени"""
        try:
            if name == 'none':
                self._active_recognizer = None
                self.recognizer_router._current_recognizer = None
                return True
            
            if name not in self._recognizer_classes:
                print(f"Unknown recognizer: {name}")
                return False
            
            # Выгружаем старый модуль
            if self._active_recognizer:
                await self._active_recognizer.unload_models()
            
            # Создаем новый экземпляр
            recognizer_class = self._recognizer_classes[name]
            self._active_recognizer = recognizer_class()
            await self._active_recognizer.initialize()
            
            # Обновляем router
            self.recognizer_router._current_recognizer = self._active_recognizer
            
            # Обновляем статус в конфиге
            self._config_data['active']['recognizer'] = name
            if name in self._config_data.get('recognizers', {}):
                self._config_data['recognizers'][name]['status'] = 'active'
            
            self._save_config()
            
            print(f"Loaded recognizer: {name}")
            return True
            
        except Exception as e:
            print(f"Failed to load recognizer {name}: {e}")
            return False

    async def _load_tracker(self, name: str) -> bool:
        """Загрузить трекер по имени"""
        try:
            if name == 'none':
                self._active_tracker = None
                self.tracker_router._current_tracker = None
                return True
            
            if name not in self._tracker_classes:
                print(f"Unknown tracker: {name}")
                return False
            
            # Выгружаем старый модуль
            if self._active_tracker:
                await self._active_tracker.unload_models()
            
            # Создаем новый экземпляр
            tracker_class = self._tracker_classes[name]
            self._active_tracker = tracker_class()
            await self._active_tracker.initialize()
            
            # Обновляем router
            self.tracker_router._current_tracker = self._active_tracker
            
            # Обновляем статус в конфиге
            self._config_data['active']['tracker'] = name
            if name in self._config_data.get('trackers', {}):
                self._config_data['trackers'][name]['status'] = 'active'
            
            self._save_config()
            
            print(f"Loaded tracker: {name}")
            return True
            
        except Exception as e:
            print(f"Failed to load tracker {name}: {e}")
            return False

    async def detect(self, image_bytes: bytes) -> list:
        """
        Детектировать лица на изображении через активный детектор
        
        Args:
            image_bytes: Байты изображения
            
        Returns:
            Список детектированных лиц
        """
        if not self._active_detector:
            return []
            
        return await self._active_detector.detect_with_embedding(image_bytes)

    async def recognize(self, face_image: bytes, category: str = None) -> dict:
        """
        Распознать лицо через активный рекогнайзер
        
        Args:
            face_image: Байты изображения лица
            category: Категория для поиска (опционально)
            
        Returns:
            Результат распознавания
        """
        if not self._active_recognizer:
            return {'error': 'No recognizer loaded'}
            
        # Извлечь эмбеддинг
        embedding = await self._active_recognizer.extract_embedding(face_image)
        
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
        Отследить лица по кадрам через активный трекер
        
        Args:
            frames: Список кадров (байты)
            
        Returns:
            Список треков
        """
        if not self._active_tracker:
            return []
            
        return await self._active_tracker.track(frames)

    async def switch_detector_async(self, name: str) -> dict:
        """
        Асинхронная версия переключения детектора (для использования внутри FastAPI)
        
        Args:
            name: Имя детектора (scrfd, yoloface, retinaface)
            
        Returns:
            Статус операции
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting switch_detector_async: {name}")
        
        success = await self._load_detector(name)
        
        logger.info(f"switch_detector_async result: {success}, name: {name}")
        
        return {
            'success': success,
            'detector': name,
            'status': 'active' if success else 'error'
        }

    async def switch_recognizer_async(self, name: str) -> dict:
        """
        Асинхронная версия переключения рекогнайзера
        
        Args:
            name: Имя рекогнайзера (arcface, adaface)
            
        Returns:
            Статус операции
        """
        success = await self._load_recognizer(name)
        
        return {
            'success': success,
            'recognizer': name,
            'status': 'active' if success else 'error'
        }

    async def switch_tracker_async(self, name: str) -> dict:
        """
        Асинхронная версия переключения трекера
        
        Args:
            name: Имя трекера (bytetrack, botsort)
            
        Returns:
            Статус операции
        """
        success = await self._load_tracker(name)
        
        return {
            'success': success,
            'tracker': name,
            'status': 'active' if success else 'error'
        }

    def get_status(self) -> dict:
        """
        Получить полный статус AI системы
        
        Returns:
            Словарь со статусом всех компонентов
        """
        # Загружаем актуальную конфигурацию
        self._config_data = self._load_config()
        
        active_detector = self._config_data.get('active', {}).get('detector', 'none')
        active_recognizer = self._config_data.get('active', {}).get('recognizer', 'none')
        active_tracker = self._config_data.get('active', {}).get('tracker', 'none')
        
        detectors = self._config_data.get('detectors', {})
        recognizers = self._config_data.get('recognizers', {})
        trackers = self._config_data.get('trackers', {})
        
        modules_status = {}
        
        # Status for all detectors
        for name in ['scrfd', 'yoloface', 'retinaface']:
            mod = detectors.get(name, {})
            mod_status = mod.get('status', 'not_installed')
            installed = mod_status != 'not_installed'
            # Also verify model file exists on disk
            model_path = mod.get('model_path')
            if installed and model_path:
                from pathlib import Path
                model_file = Path(__file__).parent.parent.parent.parent / model_path
                installed = model_file.exists()
            modules_status[name] = {
                'installed': installed,
                'loaded': name == active_detector and installed,
                'active': name == active_detector and installed,
                'version': mod.get('version') if installed else None,
                'provider': mod.get('provider'),
            }
        
        # Status for all recognizers
        for name in ['arcface', 'adaface']:
            mod = recognizers.get(name, {})
            mod_status = mod.get('status', 'not_instaled')
            installed = mod_status != 'not_installed'
            model_path = mod.get('model_path')
            if installed and model_path:
                from pathlib import Path
                model_file = Path(__file__).parent.parent.parent.parent / model_path
                installed = model_file.exists()
            modules_status[name] = {
                'installed': installed,
                'loaded': name == active_recognizer and installed,
                'active': name == active_recognizer and installed,
                'version': mod.get('version') if installed else None,
                'provider': mod.get('provider'),
            }
        
        # Status for all trackers
        for name in ['bytetrack', 'botsort']:
            mod = trackers.get(name, {})
            mod_status = mod.get('status', 'not_installed')
            installed = mod_status != 'not_installed'
            modules_status[name] = {
                'installed': installed,
                'loaded': name == active_tracker and installed,
                'active': name == active_tracker and installed,
                'version': mod.get('version') if installed else None,
                'provider': mod.get('provider'),
            }
        
        return {
            'active': {
                'detector': active_detector,
                'recognizer': active_recognizer,
                'tracker': active_tracker,
            },
            'modules': modules_status,
        }
