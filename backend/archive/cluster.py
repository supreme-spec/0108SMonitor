"""
Clustering Module for Batch Processing

Группировка лиц внутри эпизода по идентичности:
- Union-Find кластеризация (связные компоненты) - ПРАВИЛЬНО
- Greedy clustering (устаревший, не использовать)
- K-means для больших наборов
- Дедупликация похожих лиц
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from .config import GLOBAL, TIERS


# ============= UNION-FIND CLUSTERER =============
class UnionFindClusterer:
    """
    Union-Find кластеризатор для группировки лиц по идентичности.
    
    Правильно работает с цепочками связей:
    A~B (0.44), B~C (0.44), C~D (0.43) => {A, B, C, D} один кластер
    
    Алгоритм:
    1. Построить матрицу похожестей
    2. Для каждой пары с cos >= t_intra - объединить множества
    3. Вернуть связные компоненты
    """
    
    def __init__(self, threshold: float = None):
        """Инициализация с порогом из config или явным значением"""
        self.threshold = threshold if threshold is not None else GLOBAL["gray_zone"][1]  # 0.45
    
    def cluster(self, embeddings: np.ndarray, 
                ids: Optional[List[int]] = None,
                threshold: float = None) -> Dict[int, List[int]]:
        """
        Кластеризация эмбеддингов через union-find
        
        Args:
            embeddings: array shape (N, D) - нормированные векторы
            ids: optional list of face IDs
            threshold: порог похожести (переопределяет из config)
        
        Returns:
            dict: cluster_id -> list of face_indices
        """
        if len(embeddings) == 0:
            return {}
        
        if ids is None:
            ids = list(range(len(embeddings)))
        
        # Нормализация (если ещё не нормированны)
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
        
        # Косинусная близость
        similarities = embeddings @ embeddings.T
        
        # Union-Find структура
        parent = list(range(len(embeddings)))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])  # path compression
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Объединение по порогу
        t = threshold if threshold is not None else self.threshold
        n = len(embeddings)
        for i in range(n):
            for j in range(i + 1, n):
                if similarities[i, j] >= t:
                    union(i, j)
        
        # Группировка по корням
        clusters = defaultdict(list)
        for i in range(n):
            root = find(i)
            clusters[root].append(ids[i])
        
        # Переиндексация
        result = {}
        for idx, (root, members) in enumerate(sorted(clusters.items())):
            result[idx] = members
        
        return result


# ============= GREEDY CLUSTERER (устаревший) =============
class GreedyClusterer:
    """
    Жадный кластеризатор (устаревший, не использовать для production).
    
    Проблема: не обрабатывает цепочки связей.
    A~B (0.44), B~C (0.44), C~D (0.43) =>
      - Greedy: {A, B}, {C, D} - разорвёт цепочку
      - UnionFind: {A, B, C, D} - правильно
    
    Оставлен для backward compatibility.
    """
    
    def __init__(self, threshold: float = None):
        self.threshold = threshold if threshold is not None else GLOBAL["gray_zone"][1]
    
    def cluster(self, embeddings: np.ndarray, 
                ids: Optional[List[int]] = None) -> Dict[int, List[int]]:
        """
        Жадная кластеризация (не рекомендуется)
        """
        if len(embeddings) == 0:
            return {}
        
        if ids is None:
            ids = list(range(len(embeddings)))
        
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
        similarities = embeddings @ embeddings.T
        
        clusters = {}
        cluster_assignments = {}
        next_cluster_id = 0
        
        for i, face_id in enumerate(ids):
            best_cluster = None
            best_sim = -1
            
            for cluster_id, members in clusters.items():
                if len(members) == 0:
                    continue
                first_member = members[0]
                sim = float(similarities[i, first_member])
                if sim > best_sim:
                    best_sim = sim
                    best_cluster = cluster_id
            
            if best_cluster is not None and best_sim >= self.threshold:
                clusters[best_cluster].append(i)
                cluster_assignments[face_id] = best_cluster
            else:
                clusters[next_cluster_id] = [i]
                cluster_assignments[face_id] = next_cluster_id
                next_cluster_id += 1
        
        return clusters


# ============= MULTI-SCALE CLUSTERER =============
class MultiScaleClusterer:
    """
    Мультискейловая кластеризация для разных тиров качества
    """
    
    def __init__(self):
        # Пороги по тирам: A строже, C мягче
        self.thresholds = {
            "A": GLOBAL["gray_zone"][1] + 0.05,  # 0.50
            "B": GLOBAL["gray_zone"][1],          # 0.45
            "C": GLOBAL["gray_zone"][1] - 0.05,   # 0.40
            "D": GLOBAL["gray_zone"][0],          # 0.25
        }
    
    def cluster_by_tier(self, embeddings: np.ndarray, 
                        tiers: List[str],
                        ids: Optional[List[int]] = None) -> Dict[str, Dict[int, List[int]]]:
        """
        Кластеризация с учётом тиров качества
        
        Returns:
            dict: tier -> cluster_id -> list of face_ids
        """
        if ids is None:
            ids = list(range(len(embeddings)))
        
        tier_indices = defaultdict(list)
        for i, tier in enumerate(tiers):
            tier_indices[tier].append(i)
        
        clusters_by_tier = {}
        
        for tier, indices in tier_indices.items():
            if tier == "D" or len(indices) == 0:
                clusters_by_tier[tier] = {idx: [idx] for idx in indices}
                continue
            
            uf = UnionFindClusterer(threshold=self.thresholds.get(tier, GLOBAL["gray_zone"][1]))
            tier_embeddings = embeddings[indices]
            tier_ids = [ids[i] for i in indices]
            
            clusters = uf.cluster(tier_embeddings, tier_ids)
            
            # Конвертируем ключи обратно к исходным индексам
            converted_clusters = {}
            for cluster_id, member_indices in clusters.items():
                converted_clusters[cluster_id] = [indices[i] for i in member_indices]
            
            clusters_by_tier[tier] = converted_clusters
        
        return clusters_by_tier


# ============= K-MEANS (для больших наборов) =============
class KMeansEmbeddings:
    """K-means кластеризация для эмбеддингов"""
    
    def __init__(self, n_clusters: int = None, max_iter: int = 100):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
    
    def fit(self, embeddings: np.ndarray) -> np.ndarray:
        """Возвращает массив меток кластеров"""
        if len(embeddings) == 0:
            return np.array([])
        
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
        
        n_samples = len(embeddings)
        n_clusters = self.n_clusters or min(10, n_samples)
        
        # K-means++ инициализация
        centers = [embeddings[np.random.randint(n_samples)]]
        for _ in range(1, n_clusters):
            distances = np.array([min(np.linalg.norm(e - c) for c in centers) for e in embeddings])
            probabilities = distances ** 2
            probabilities /= probabilities.sum()
            next_center = embeddings[np.random.choice(n_samples, p=probabilities)]
            centers.append(next_center)
        
        centers = np.array(centers)
        
        labels = np.zeros(n_samples, dtype=int)
        for _ in range(self.max_iter):
            new_labels = np.argmax(centers @ embeddings.T, axis=0)
            if np.array_equal(labels, new_labels):
                break
            labels = new_labels
            
            for k in range(n_clusters):
                mask = labels == k
                if mask.sum() > 0:
                    centers[k] = embeddings[mask].mean(axis=0)
        
        return labels


# ============= UTILITY FUNCTIONS =============
def deduplicate_faces(embeddings: np.ndarray, 
                      threshold: float = None) -> Tuple[np.ndarray, Dict[int, int]]:
    """
    Дедупликация почти одинаковых лиц (дубли одной сессии)
    
    Args:
        embeddings: нормированные векторы
        threshold: порог похожести (по умолчанию dedup_same_photo из config)
    
    Returns:
        (unique_embeddings, mapping: old_idx -> new_idx)
    """
    if threshold is None:
        threshold = GLOBAL.get("dedup_same_photo", 0.95)
    
    if len(embeddings) == 0:
        return embeddings, {}
    
    embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
    similarities = embeddings @ embeddings.T
    n = len(embeddings)
    
    to_remove = set()
    mapping = list(range(n))
    
    for i in range(n):
        if i in to_remove:
            continue
        for j in range(i + 1, n):
            if j in to_remove:
                continue
            if similarities[i, j] > threshold:
                to_remove.add(j)
                mapping[j] = i
    
    unique_mask = np.array([i not in to_remove for i in range(n)])
    unique_embeddings = embeddings[unique_mask]
    unique_mapping = {i: mapping[i] for i in range(n) if i not in to_remove}
    
    return unique_embeddings, unique_mapping


def merge_clusters_by_similarity(clusters: Dict[int, List[int]], 
                                  embeddings: np.ndarray,
                                  threshold: float = None) -> Dict[int, List[int]]:
    """
    Слияние кластеров, если средняя похожесть между ними > threshold
    """
    if threshold is None:
        threshold = GLOBAL.get("t_cross", 0.45) + 0.2  # 0.65 default
    
    if len(clusters) <= 1:
        return clusters
    
    embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
    
    cluster_vectors = {}
    for cid, members in clusters.items():
        cluster_vectors[cid] = embeddings[members].mean(axis=0)
    
    cluster_ids = list(clusters.keys())
    n_clusters = len(cluster_ids)
    
    merged = False
    new_clusters = clusters.copy()
    
    for i in range(n_clusters):
        if cluster_ids[i] not in new_clusters:
            continue
        for j in range(i + 1, n_clusters):
            if cluster_ids[j] not in new_clusters:
                continue
            
            sim = float(np.dot(cluster_vectors[cluster_ids[i]], cluster_vectors[cluster_ids[j]]))
            
            if sim >= threshold:
                new_clusters[cluster_ids[i]].extend(new_clusters[cluster_ids[j]])
                del new_clusters[cluster_ids[j]]
                merged = True
                break
        
        if merged:
            break
    
    if merged:
        return merge_clusters_by_similarity(new_clusters, embeddings, threshold)
    
    return new_clusters


# ============= SELECTED CLUSTERER =============
# Использовать UnionFindClusterer по умолчанию
Clusterer = UnionFindClusterer


# Пример использования
if __name__ == "__main__":
    # Пример: 10 лиц, 3 человека в цепочке
    np.random.seed(42)
    
    embeddings = []
    for person in range(3):
        base = np.random.randn(512)
        base = base / np.linalg.norm(base)
        for _ in range(3 + person):
            noise = np.random.randn(512) * 0.05
            emb = base + noise
            emb = emb / np.linalg.norm(emb)
            embeddings.append(emb)
    
    embeddings = np.array(embeddings)
    
    # Union-Find кластеризация
    clusterer = UnionFindClusterer(threshold=0.55)
    clusters = clusterer.cluster(embeddings)
    
    print(f"Union-Find: Found {len(clusters)} clusters")
    for cid, members in clusters.items():
        print(f"  Cluster {cid}: {len(members)} faces")
