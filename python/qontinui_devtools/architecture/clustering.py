"""Clustering algorithm for grouping methods by semantic similarity.

from typing import Any, Any

This module implements a keyword-based clustering algorithm that groups methods
with similar responsibilities together based on their naming patterns.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass

from .semantic_utils import (
    RESPONSIBILITY_PATTERNS,
    calculate_cluster_similarity,
    calculate_similarity_score,
    classify_method,
    extract_keywords,
)
from typing import Any


@dataclass
class MethodCluster:
    """A cluster of related methods representing a responsibility.

    Attributes:
        name: Descriptive name of the responsibility (e.g., "Data Access")
        methods: List of method names in this cluster
        keywords: Set of common keywords across methods
        confidence: Confidence score (0-1) for this being a real responsibility
    """

    name: str
    methods: list[str]
    keywords: set[str]
    confidence: float

    def __post_init__(self) -> None:
        """Ensure methods is a list and keywords is a set."""
        if not isinstance(self.methods, list):
            self.methods = list(self.methods)
        if not isinstance(self.keywords, set):
            self.keywords = set(self.keywords)


def cluster_methods_by_keywords(
    methods: list[str], min_cluster_size: int = 2
) -> list[MethodCluster]:
    """Cluster methods by keyword similarity.

    Algorithm:
    1. Classify each method into a responsibility category
    2. Group methods by their classification
    3. For unclassified methods, use similarity-based clustering
    4. Name clusters based on common patterns
    5. Calculate confidence scores

    Args:
        methods: List of method names to cluster
        min_cluster_size: Minimum number of methods to form a cluster

    Returns:
        List of method clusters representing different responsibilities
    """
    if not methods:
        return []

    # Step 1: Classify methods by responsibility patterns
    classified: dict[str, list[str]] = defaultdict(list)

    for method in methods:
        category = classify_method(method)
        classified[category].append(method)

    # Step 2: Create clusters from classifications
    clusters: list[MethodCluster] = []

    for category, method_list in classified.items():
        if category == "Other":
            # Handle unclassified methods separately
            continue

        if len(method_list) >= min_cluster_size:
            # Aggregate keywords
            all_keywords = set()
            for method in method_list:
                all_keywords.update(extract_keywords(method))

            # Calculate confidence based on cluster size and keyword overlap
            confidence = _calculate_cluster_confidence(method_list, all_keywords)

            clusters.append(
                MethodCluster(
                    name=category,
                    methods=method_list,
                    keywords=all_keywords,
                    confidence=confidence,
                )
            )

    # Step 3: Handle "Other" methods with similarity-based clustering
    if "Other" in classified and classified["Other"]:
        other_methods = classified["Other"]
        other_clusters = _cluster_by_similarity(other_methods, min_cluster_size)
        clusters.extend(other_clusters)

    # Step 4: Merge similar clusters
    clusters = merge_similar_clusters(clusters, threshold=0.6)

    # Sort clusters by size (largest first)
    clusters.sort(key=lambda c: len(c.methods), reverse=True)

    return clusters


def _cluster_by_similarity(methods: list[str], min_cluster_size: int) -> list[MethodCluster]:
    """Cluster methods using similarity-based approach.

    Uses a simple greedy algorithm to group similar methods together.

    Args:
        methods: List of method names
        min_cluster_size: Minimum cluster size

    Returns:
        List of method clusters
    """
    if len(methods) < min_cluster_size:
        return []

    clusters: list[MethodCluster] = []
    unclustered = set(methods)

    while unclustered:
        # Start a new cluster with the first unclustered method
        seed = next(iter(unclustered))
        cluster_methods = [seed]
        unclustered.remove(seed)

        # Find similar methods
        to_remove = set()
        for method in unclustered:
            # Check similarity with all methods in current cluster
            similarities = [calculate_similarity_score(method, m) for m in cluster_methods]
            avg_similarity = sum(similarities) / len(similarities)

            if avg_similarity > 0.3:  # Threshold for similarity
                cluster_methods.append(method)
                to_remove.add(method)

        unclustered -= to_remove

        # Only create cluster if it meets minimum size
        if len(cluster_methods) >= min_cluster_size:
            all_keywords = set()
            for method in cluster_methods:
                all_keywords.update(extract_keywords(method))

            cluster_name = name_cluster(cluster_methods)
            confidence = _calculate_cluster_confidence(cluster_methods, all_keywords)

            clusters.append(
                MethodCluster(
                    name=cluster_name,
                    methods=cluster_methods,
                    keywords=all_keywords,
                    confidence=confidence,
                )
            )

    return clusters


def _calculate_cluster_confidence(methods: list[str], keywords: set[str]) -> float:
    """Calculate confidence score for a cluster.

    Confidence is based on:
    - Number of methods (more = higher confidence)
    - Keyword overlap (more shared keywords = higher confidence)
    - Naming consistency

    Args:
        methods: List of method names in cluster
        keywords: Set of keywords across all methods

    Returns:
        Confidence score between 0 and 1
    """
    if not methods:
        return 0.0

    # Factor 1: Cluster size (normalized)
    size_score = min(len(methods) / 10.0, 1.0)  # Cap at 10 methods

    # Factor 2: Keyword density (keywords per method)
    keyword_density = len(keywords) / len(methods) if methods else 0
    density_score = min(keyword_density / 3.0, 1.0)  # Cap at 3 keywords/method

    # Factor 3: Naming consistency (how many methods share common prefix)
    prefixes = [extract_keywords(m) for m in methods]
    common_keywords = set.intersection(*prefixes) if prefixes else set()
    consistency_score = len(common_keywords) / len(keywords) if keywords else 0

    # Weighted average
    confidence = size_score * 0.4 + density_score * 0.3 + consistency_score * 0.3

    return confidence


def merge_similar_clusters(
    clusters: list[MethodCluster], threshold: float = 0.7
) -> list[MethodCluster]:
    """Merge clusters that are very similar.

    Args:
        clusters: List of method clusters
        threshold: Similarity threshold for merging (0-1)

    Returns:
        List of merged clusters
    """
    if len(clusters) <= 1:
        return clusters

    merged: list[Any] = []
    used = set()

    for i, cluster1 in enumerate(clusters):
        if i in used:
            continue

        # Start with this cluster
        combined_methods = list(cluster1.methods)
        combined_keywords = set(cluster1.keywords)

        # Find similar clusters to merge
        for j, cluster2 in enumerate(clusters[i + 1 :], start=i + 1):
            if j in used:
                continue

            similarity = calculate_cluster_similarity(cluster1.methods, cluster2.methods)

            if similarity >= threshold:
                combined_methods.extend(cluster2.methods)
                combined_keywords.update(cluster2.keywords)
                used.add(j)

        # Create merged cluster
        cluster_name = name_cluster(combined_methods)
        confidence = _calculate_cluster_confidence(combined_methods, combined_keywords)

        merged.append(
            MethodCluster(
                name=cluster_name,
                methods=combined_methods,
                keywords=combined_keywords,
                confidence=confidence,
            )
        )
        used.add(i)

    return merged


def name_cluster(methods: list[str]) -> str:
    """Generate descriptive name for cluster.

    Analyzes the methods to determine the best name based on:
    - Common responsibility patterns
    - Most frequent keywords
    - Common prefixes

    Args:
        methods: List of method names in cluster

    Returns:
        Descriptive name for the cluster
    """
    if not methods:
        return "Unknown"

    # Try to classify based on most common category
    categories = [classify_method(m) for m in methods]
    category_counts = Counter(categories)

    # If a clear category emerges (excluding "Other")
    most_common = category_counts.most_common(2)
    if most_common and most_common[0][0] != "Other":
        if most_common[0][1] >= len(methods) * 0.5:  # At least 50% agreement
            return most_common[0][0]

    # Fall back to keyword analysis
    all_keywords: list[Any] = []
    for method in methods:
        all_keywords.extend(extract_keywords(method))

    if not all_keywords:
        return "Other"

    keyword_counts = Counter(all_keywords)
    most_common_keywords = [kw for kw, _ in keyword_counts.most_common(3)]

    # Check if top keywords match responsibility patterns
    for responsibility, patterns in RESPONSIBILITY_PATTERNS.items():
        for keyword in most_common_keywords:
            if keyword in patterns:
                return responsibility

    # Create name from top keywords
    if len(most_common_keywords) >= 2:
        return f"{most_common_keywords[0].title()} {most_common_keywords[1].title()}"
    elif most_common_keywords:
        return f"{most_common_keywords[0].title()} Operations"

    return "Other"


def analyze_cluster_cohesion(cluster: MethodCluster) -> float:
    """Analyze how cohesive a cluster is.

    A cohesive cluster has methods that are highly similar to each other.

    Args:
        cluster: Method cluster to analyze

    Returns:
        Cohesion score between 0 and 1
    """
    if len(cluster.methods) < 2:
        return 1.0  # Single method is perfectly cohesive

    similarities: list[Any] = []
    methods = cluster.methods

    # Calculate pairwise similarities
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            sim = calculate_similarity_score(methods[i], methods[j])
            similarities.append(sim)

    # Average similarity
    return sum(similarities) / len(similarities) if similarities else 0.0
