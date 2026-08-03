"""
AI Module Infrastructure

Этот пакет содержит все AI-модули системы распознавания лиц:
- Detectors (детекторы лиц)
- Recognizers (распознавание)
- Trackers (трекинг)
- Databases (поиск по эмбеддингам)
- Router (маршрутизация)
- Utils (утилиты)
"""

from .base import BaseModule, ModuleStatus, ModuleType

__all__ = ['BaseModule', 'ModuleStatus', 'ModuleType']
