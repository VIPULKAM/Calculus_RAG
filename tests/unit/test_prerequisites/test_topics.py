"""
Tests for topic catalog/definitions.

TDD: These tests define the expected behavior before implementation.
"""

import pytest


class TestTopicCatalog:
    """Test the topic catalog."""

    def test_load_calculus_topics(self) -> None:
        """Should load predefined calculus topics."""
        from calculus_rag.prerequisites.topics import get_calculus_topics

        topics = get_calculus_topics()

        assert len(topics) > 0
        assert "limits.introduction" in topics
        assert "derivatives.power_rule" in topics

    def test_topic_has_metadata(self) -> None:
        """Each topic should have metadata."""
        from calculus_rag.prerequisites.topics import get_calculus_topics

        topics = get_calculus_topics()

        for topic_id, topic_data in topics.items():
            assert "display_name" in topic_data
            assert "description" in topic_data
            assert "difficulty" in topic_data
            assert "prerequisites" in topic_data

    def test_build_prerequisite_graph_from_catalog(self) -> None:
        """Should build a prerequisite graph from the topic catalog."""
        from calculus_rag.prerequisites.topics import build_prerequisite_graph

        graph = build_prerequisite_graph()

        # Check that common topics are in the graph
        assert "algebra.factoring" in graph.get_all_topics()
        assert "limits.introduction" in graph.get_all_topics()
        assert "derivatives.basic" in graph.get_all_topics()

    def test_get_topic_info(self) -> None:
        """Should retrieve information about a specific topic."""
        from calculus_rag.prerequisites.topics import get_topic_info

        topic = get_topic_info("limits.introduction")

        assert topic is not None
        assert topic["display_name"] is not None
        assert topic["difficulty"] >= 1
        assert isinstance(topic["prerequisites"], list)

    def test_get_nonexistent_topic(self) -> None:
        """Should return None for non-existent topics."""
        from calculus_rag.prerequisites.topics import get_topic_info

        topic = get_topic_info("nonexistent.topic")

        assert topic is None

    def test_list_topics_by_difficulty(self) -> None:
        """Should list topics filtered by difficulty."""
        from calculus_rag.prerequisites.topics import get_topics_by_difficulty

        easy_topics = get_topics_by_difficulty(difficulty=1)
        hard_topics = get_topics_by_difficulty(difficulty=5)

        assert len(easy_topics) > 0
        assert all(topic["difficulty"] == 1 for topic in easy_topics)

    def test_search_topics(self) -> None:
        """Should search topics by keyword."""
        from calculus_rag.prerequisites.topics import search_topics

        results = search_topics("derivative")

        assert len(results) > 0
        assert any("derivative" in topic["display_name"].lower() for topic in results)
