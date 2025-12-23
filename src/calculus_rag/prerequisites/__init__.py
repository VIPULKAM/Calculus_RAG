"""Prerequisite graph and gap detection for learning paths."""

from calculus_rag.prerequisites.detector import GapAnalysis, GapDetector
from calculus_rag.prerequisites.graph import CircularDependencyError, PrerequisiteGraph
from calculus_rag.prerequisites.topics import (
    build_prerequisite_graph,
    get_calculus_topics,
    get_topic_info,
    search_topics,
)

__all__ = [
    "PrerequisiteGraph",
    "CircularDependencyError",
    "GapDetector",
    "GapAnalysis",
    "build_prerequisite_graph",
    "get_calculus_topics",
    "get_topic_info",
    "search_topics",
]
