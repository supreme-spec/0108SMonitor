"""
Router package

Маршрутизация запросов между модулями:
- DetectorRouter
- RecognizerRouter
- TrackerRouter
"""

from .detector_router import DetectorRouter
from .recognizer_router import RecognizerRouter
from .tracker_router import TrackerRouter

__all__ = ['DetectorRouter', 'RecognizerRouter', 'TrackerRouter']
