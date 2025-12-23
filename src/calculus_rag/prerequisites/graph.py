"""
Prerequisite graph for topic dependencies.

Manages the relationships between topics and their prerequisites,
enabling prerequisite checking and learning path generation.
"""

import json
from typing import Any


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in the prerequisite graph."""

    pass


class PrerequisiteGraph:
    """
    Directed acyclic graph (DAG) of topic prerequisites.

    Manages topic dependencies and provides utilities for:
    - Checking if prerequisites are met
    - Finding missing prerequisites
    - Generating learning paths
    - Topological sorting
    """

    def __init__(self) -> None:
        """Initialize an empty prerequisite graph."""
        # topic -> list of prerequisite topics
        self._graph: dict[str, list[str]] = {}

    def add_topic(self, topic: str, prerequisites: list[str]) -> None:
        """
        Add a topic with its prerequisites.

        Args:
            topic: The topic identifier.
            prerequisites: List of prerequisite topic identifiers.

        Raises:
            CircularDependencyError: If adding this topic creates a cycle.
        """
        # Check for circular dependencies before adding
        if self._would_create_cycle(topic, prerequisites):
            raise CircularDependencyError(
                f"Adding {topic} with prerequisites {prerequisites} would create a cycle"
            )

        self._graph[topic] = prerequisites

    def get_all_topics(self) -> list[str]:
        """
        Get all topics in the graph.

        Returns:
            list[str]: List of all topic identifiers.
        """
        return list(self._graph.keys())

    def get_prerequisites(self, topic: str) -> list[str]:
        """
        Get direct prerequisites for a topic.

        Args:
            topic: The topic identifier.

        Returns:
            list[str]: List of prerequisite topic identifiers.
        """
        return self._graph.get(topic, [])

    def get_all_prerequisites(self, topic: str) -> list[str]:
        """
        Get all prerequisites recursively (transitive closure).

        Args:
            topic: The topic identifier.

        Returns:
            list[str]: List of all prerequisite topics (direct and indirect).
        """
        visited = set()
        self._collect_prerequisites(topic, visited)
        visited.discard(topic)  # Don't include the topic itself
        return list(visited)

    def _collect_prerequisites(self, topic: str, visited: set[str]) -> None:
        """Recursively collect all prerequisites."""
        if topic in visited or topic not in self._graph:
            return

        visited.add(topic)

        for prereq in self._graph[topic]:
            self._collect_prerequisites(prereq, visited)

    def get_dependents(self, topic: str) -> list[str]:
        """
        Get topics that depend on this topic.

        Args:
            topic: The topic identifier.

        Returns:
            list[str]: Topics that have this topic as a prerequisite.
        """
        dependents = []
        for t, prereqs in self._graph.items():
            if topic in prereqs:
                dependents.append(t)
        return dependents

    def are_prerequisites_met(self, topic: str, completed: set[str]) -> bool:
        """
        Check if all prerequisites for a topic are met.

        Args:
            topic: The topic identifier.
            completed: Set of completed topic identifiers.

        Returns:
            bool: True if all prerequisites are completed.
        """
        all_prereqs = set(self.get_all_prerequisites(topic))
        return all_prereqs.issubset(completed)

    def get_missing_prerequisites(self, topic: str, completed: set[str]) -> list[str]:
        """
        Get prerequisites that are not yet completed.

        Args:
            topic: The topic identifier.
            completed: Set of completed topic identifiers.

        Returns:
            list[str]: List of missing prerequisite topics.
        """
        all_prereqs = set(self.get_all_prerequisites(topic))
        missing = all_prereqs - completed
        return list(missing)

    def topological_sort(self) -> list[str]:
        """
        Return topics in dependency order (prerequisites first).

        Uses Kahn's algorithm for topological sorting.

        Returns:
            list[str]: Topics sorted such that prerequisites come before dependents.
        """
        # Calculate in-degrees
        in_degree = {topic: 0 for topic in self._graph}

        for prereqs in self._graph.values():
            for prereq in prereqs:
                if prereq in in_degree:
                    in_degree[prereq] += 0  # Just ensure it exists
                # Count how many topics depend on this prereq
                for topic in self._graph:
                    if prereq in self._graph[topic]:
                        in_degree[prereq] = in_degree.get(prereq, 0) + 1

        # Recalculate properly
        in_degree = {topic: 0 for topic in self._graph}
        for topic, prereqs in self._graph.items():
            for prereq in prereqs:
                in_degree[topic] = in_degree.get(topic, 0) + 1

        # Start with topics that have no prerequisites
        queue = [topic for topic, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            topic = queue.pop(0)
            result.append(topic)

            # Reduce in-degree for dependents
            for dependent in self.get_dependents(topic):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    def get_learning_path(self, target_topic: str, completed: set[str]) -> list[str]:
        """
        Generate a learning path to reach the target topic.

        Args:
            target_topic: The topic to learn.
            completed: Set of already completed topics.

        Returns:
            list[str]: Ordered list of topics to learn (prerequisites first).
        """
        # Get all prerequisites needed
        all_prereqs = self.get_all_prerequisites(target_topic)

        # Filter out already completed
        needed = [p for p in all_prereqs if p not in completed]

        # Add target topic
        needed.append(target_topic)

        # Sort by dependencies
        sorted_all = self.topological_sort()

        # Filter to only needed topics, maintaining order
        path = [t for t in sorted_all if t in needed]

        return path

    def _would_create_cycle(self, new_topic: str, new_prerequisites: list[str]) -> bool:
        """
        Check if adding a topic with prerequisites would create a cycle.

        Args:
            new_topic: Topic to add.
            new_prerequisites: Its prerequisites.

        Returns:
            bool: True if adding would create a cycle.
        """
        # Temporarily add to graph
        temp_graph = self._graph.copy()
        temp_graph[new_topic] = new_prerequisites

        # Try to do topological sort with DFS cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(topic: str) -> bool:
            visited.add(topic)
            rec_stack.add(topic)

            for prereq in temp_graph.get(topic, []):
                if prereq not in visited:
                    if has_cycle(prereq):
                        return True
                elif prereq in rec_stack:
                    return True

            rec_stack.remove(topic)
            return False

        for topic in temp_graph:
            if topic not in visited:
                if has_cycle(topic):
                    return True

        return False

    def to_dict(self) -> dict[str, list[str]]:
        """
        Serialize graph to dictionary.

        Returns:
            dict: Graph as a dictionary.
        """
        return self._graph.copy()

    @classmethod
    def from_dict(cls, data: dict[str, list[str]]) -> "PrerequisiteGraph":
        """
        Load graph from dictionary.

        Args:
            data: Dictionary of topic -> prerequisites.

        Returns:
            PrerequisiteGraph: New graph instance.
        """
        graph = cls()
        graph._graph = data.copy()
        return graph

    def to_json(self) -> str:
        """
        Serialize graph to JSON string.

        Returns:
            str: JSON representation of the graph.
        """
        return json.dumps(self._graph, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "PrerequisiteGraph":
        """
        Load graph from JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            PrerequisiteGraph: New graph instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return f"PrerequisiteGraph(topics={len(self._graph)})"
