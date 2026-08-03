"""
Database package

Модули поиска по эмбеддингам:
- FAISS (ACTUAL)
- В будущем: HNSW, IVF-Adam
"""

from .faiss import FAISS

__all__ = ['FAISS']
