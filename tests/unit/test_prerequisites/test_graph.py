"""
Tests for prerequisite graph.

TDD: These tests define the expected behavior before implementation.
"""

import pytest


class TestPrerequisiteGraph:
    """Test the PrerequisiteGraph class."""

    def test_create_empty_graph(self) -> None:
        """Should create an empty prerequisite graph."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()

        assert graph is not None
        assert len(graph.get_all_topics()) == 0

    def test_add_topic_without_prerequisites(self) -> None:
        """Should add a topic with no prerequisites."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.factoring", prerequisites=[])

        assert "algebra.factoring" in graph.get_all_topics()
        assert graph.get_prerequisites("algebra.factoring") == []

    def test_add_topic_with_prerequisites(self) -> None:
        """Should add a topic with prerequisites."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.factoring", prerequisites=[])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        prereqs = graph.get_prerequisites("limits.introduction")
        assert "algebra.factoring" in prereqs

    def test_get_all_prerequisites_recursive(self) -> None:
        """Should get all prerequisites recursively."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.basics", prerequisites=[])
        graph.add_topic("algebra.factoring", prerequisites=["algebra.basics"])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        # Get all prerequisites for limits (should include factoring AND basics)
        all_prereqs = graph.get_all_prerequisites("limits.introduction")

        assert "algebra.factoring" in all_prereqs
        assert "algebra.basics" in all_prereqs

    def test_detect_circular_dependency(self) -> None:
        """Should detect circular dependencies."""
        from calculus_rag.prerequisites.graph import CircularDependencyError, PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("topic_a", prerequisites=["topic_b"])

        # Adding topic_b with topic_a as prereq creates a cycle
        with pytest.raises(CircularDependencyError):
            graph.add_topic("topic_b", prerequisites=["topic_a"])

    def test_get_dependents(self) -> None:
        """Should get topics that depend on a given topic."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.factoring", prerequisites=[])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])
        graph.add_topic("limits.advanced", prerequisites=["algebra.factoring"])

        # Topics that depend on factoring
        dependents = graph.get_dependents("algebra.factoring")

        assert "limits.introduction" in dependents
        assert "limits.advanced" in dependents

    def test_topological_sort(self) -> None:
        """Should return topics in dependency order."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.basics", prerequisites=[])
        graph.add_topic("algebra.factoring", prerequisites=["algebra.basics"])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        sorted_topics = graph.topological_sort()

        # algebra.basics should come before factoring
        basics_idx = sorted_topics.index("algebra.basics")
        factoring_idx = sorted_topics.index("algebra.factoring")
        limits_idx = sorted_topics.index("limits.introduction")

        assert basics_idx < factoring_idx < limits_idx

    def test_check_prerequisites_met(self) -> None:
        """Should check if prerequisites are met for a topic."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.factoring", prerequisites=[])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        # If factoring is completed, limits prereqs are met
        completed = {"algebra.factoring"}
        assert graph.are_prerequisites_met("limits.introduction", completed)

        # If factoring is not completed, limits prereqs are not met
        completed = set()
        assert not graph.are_prerequisites_met("limits.introduction", completed)

    def test_get_missing_prerequisites(self) -> None:
        """Should return missing prerequisites for a topic."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.basics", prerequisites=[])
        graph.add_topic("algebra.factoring", prerequisites=["algebra.basics"])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        completed = {"algebra.basics"}  # Only basics is completed

        missing = graph.get_missing_prerequisites("limits.introduction", completed)

        # Should need factoring (even though basics is done)
        assert "algebra.factoring" in missing
        assert "algebra.basics" not in missing  # Already completed


class TestPrerequisiteGraphPersistence:
    """Test saving and loading prerequisite graphs."""

    def test_to_dict(self) -> None:
        """Should serialize graph to dictionary."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.factoring", prerequisites=[])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        data = graph.to_dict()

        assert "algebra.factoring" in data
        assert "limits.introduction" in data
        assert data["limits.introduction"] == ["algebra.factoring"]

    def test_from_dict(self) -> None:
        """Should load graph from dictionary."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        data = {
            "algebra.factoring": [],
            "limits.introduction": ["algebra.factoring"],
        }

        graph = PrerequisiteGraph.from_dict(data)

        assert "algebra.factoring" in graph.get_all_topics()
        assert graph.get_prerequisites("limits.introduction") == ["algebra.factoring"]

    def test_to_json(self) -> None:
        """Should serialize graph to JSON string."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.factoring", prerequisites=[])

        json_str = graph.to_json()

        assert "algebra.factoring" in json_str
        assert isinstance(json_str, str)

    def test_from_json(self) -> None:
        """Should load graph from JSON string."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        json_str = '{"algebra.factoring": [], "limits.introduction": ["algebra.factoring"]}'

        graph = PrerequisiteGraph.from_json(json_str)

        assert "algebra.factoring" in graph.get_all_topics()
        assert "limits.introduction" in graph.get_all_topics()


class TestPrerequisiteGraphAdvanced:
    """Test advanced graph operations."""

    def test_get_learning_path(self) -> None:
        """Should suggest a learning path to reach a topic."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.basics", prerequisites=[])
        graph.add_topic("algebra.factoring", prerequisites=["algebra.basics"])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])
        graph.add_topic("derivatives.basic", prerequisites=["limits.introduction"])

        completed = set()  # Student has completed nothing

        # Get path to learn derivatives
        path = graph.get_learning_path("derivatives.basic", completed)

        # Should suggest: basics -> factoring -> limits -> derivatives
        assert len(path) == 4
        assert path[0] == "algebra.basics"
        assert path[-1] == "derivatives.basic"

    def test_get_learning_path_with_partial_completion(self) -> None:
        """Should suggest path considering what's already completed."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.basics", prerequisites=[])
        graph.add_topic("algebra.factoring", prerequisites=["algebra.basics"])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring"])

        completed = {"algebra.basics", "algebra.factoring"}  # Already done

        path = graph.get_learning_path("limits.introduction", completed)

        # Should only suggest limits (others already done)
        assert path == ["limits.introduction"]
