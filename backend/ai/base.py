"""
Базовые классы для AI модулей
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class ModuleType(Enum):
    DETECTOR = "detector"
    RECOGNIZER = "recognizer"
    TRACKER = "tracker"
    DATABASE = "database"
    ROUTER = "router"
    UTIL = "util"


class ModuleStatus(Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class ModuleInfo:
    name: str
    type: ModuleType
    version: Optional[str]
    provider: str  # CPU/GPU
    enabled: bool
    status: ModuleStatus
    description: str = ""
    priority: int = 0
    gpu_required: bool = False
    models: list = None

    def __post_init__(self):
        if self.models is None:
            self.models = []


class BaseModule(ABC):
    """Базовый класс для всех AI модулей"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.status = ModuleStatus.NOT_INSTALLED
        self.version: Optional[str] = None
        self.info: Optional[ModuleInfo] = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Инициализация модуля. Возвращает True если успешно."""
        pass

    @abstractmethod
    async def load_models(self) -> bool:
        """Загрузка моделей. Возвращает True если успешно."""
        pass

    @abstractmethod
    async def unload_models(self) -> bool:
        """Выгрузка моделей. Возвращает True если успешно."""
        pass

    def get_info(self) -> ModuleInfo:
        """Возвращает информацию о модуле"""
        return self.info

    def is_active(self) -> bool:
        """Проверяет, активен ли модуль"""
        return self.status == ModuleStatus.ACTIVE

    def get_status(self) -> str:
        """Возвращает строковое представление статуса"""
        return self.status.value
