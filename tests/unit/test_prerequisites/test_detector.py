"""
Tests for prerequisite gap detection.

TDD: These tests define the expected behavior before implementation.
"""

import pytest


class TestGapDetector:
    """Test the GapDetector class."""

    @pytest.fixture
    def sample_graph(self):
        """Create a sample prerequisite graph for testing."""
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("algebra.basics", prerequisites=[])
        graph.add_topic("algebra.factoring", prerequisites=["algebra.basics"])
        graph.add_topic("functions.notation", prerequisites=["algebra.basics"])
        graph.add_topic("functions.composition", prerequisites=["functions.notation"])
        graph.add_topic("limits.introduction", prerequisites=["algebra.factoring", "functions.notation"])
        graph.add_topic("derivatives.basic", prerequisites=["limits.introduction"])
        graph.add_topic("derivatives.chain_rule", prerequisites=["derivatives.basic", "functions.composition"])

        return graph

    def test_create_gap_detector(self, sample_graph) -> None:
        """Should create a gap detector with a prerequisite graph."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)

        assert detector is not None

    def test_detect_gaps_no_completion(self, sample_graph) -> None:
        """Should detect all prerequisites as gaps when nothing is completed."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)
        completed_topics = set()

        gaps = detector.detect_gaps("derivatives.chain_rule", completed_topics)

        # Should need everything: basics, factoring, notation, composition, limits, basic derivatives
        assert len(gaps) > 0
        assert "algebra.basics" in gaps
        assert "functions.composition" in gaps

    def test_detect_gaps_partial_completion(self, sample_graph) -> None:
        """Should only detect missing prerequisites."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)
        completed_topics = {
            "algebra.basics",
            "algebra.factoring",
            "functions.notation",
        }

        gaps = detector.detect_gaps("derivatives.chain_rule", completed_topics)

        # Should still need: composition, limits, basic derivatives
        assert "functions.composition" in gaps
        assert "limits.introduction" in gaps
        assert "derivatives.basic" in gaps

        # Should NOT need already completed
        assert "algebra.basics" not in gaps
        assert "algebra.factoring" not in gaps

    def test_detect_gaps_all_completed(self, sample_graph) -> None:
        """Should detect no gaps when all prerequisites are met."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)
        completed_topics = {
            "algebra.basics",
            "algebra.factoring",
            "functions.notation",
            "functions.composition",
            "limits.introduction",
            "derivatives.basic",
        }

        gaps = detector.detect_gaps("derivatives.chain_rule", completed_topics)

        assert len(gaps) == 0

    def test_detect_critical_gaps(self, sample_graph) -> None:
        """Should identify the most critical gaps to address first."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)
        completed_topics = set()

        critical_gaps = detector.detect_critical_gaps("derivatives.chain_rule", completed_topics)

        # Critical gaps should be the foundational ones (no prerequisites themselves)
        assert "algebra.basics" in critical_gaps
        # Should NOT include higher-level topics that depend on basics
        assert "derivatives.basic" not in critical_gaps

    def test_analyze_query_detects_topic(self) -> None:
        """Should analyze a query and detect the topic being asked about."""
        from calculus_rag.prerequisites.detector import GapDetector
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("derivatives.chain_rule", prerequisites=[])

        detector = GapDetector(graph)

        query = "How do I find the derivative of sin(x^2)?"
        detected_topic = detector.analyze_query(query)

        # Should detect chain rule topic
        assert detected_topic == "derivatives.chain_rule"

    def test_analyze_query_with_keywords(self) -> None:
        """Should detect topic from keywords in query."""
        from calculus_rag.prerequisites.detector import GapDetector
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        graph.add_topic("limits.introduction", prerequisites=[])

        detector = GapDetector(graph)

        query = "What is a limit?"
        detected_topic = detector.analyze_query(query)

        assert detected_topic == "limits.introduction"

    def test_detect_confusion_signals(self) -> None:
        """Should detect signals of confusion in queries."""
        from calculus_rag.prerequisites.detector import GapDetector
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        graph = PrerequisiteGraph()
        detector = GapDetector(graph)

        confused_queries = [
            "I don't understand how to do this",
            "What is a derivative?",  # Very basic question
            "I'm confused about limits",
            "Can you explain this again?",
        ]

        for query in confused_queries:
            assert detector.has_confusion_signals(query)

        clear_queries = [
            "Find the derivative of x^2",
            "Solve this integral",
        ]

        for query in clear_queries:
            assert not detector.has_confusion_signals(query)

    def test_suggest_prerequisite_review(self, sample_graph) -> None:
        """Should suggest which prerequisites to review."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)
        completed_topics = {"algebra.basics"}

        suggestions = detector.suggest_review(
            target_topic="derivatives.chain_rule",
            completed_topics=completed_topics,
        )

        assert len(suggestions) > 0
        # Should suggest reviewing factoring before moving to derivatives
        assert any("factoring" in s.lower() or "algebra" in s.lower() for s in suggestions)

    def test_get_next_topic_to_learn(self, sample_graph) -> None:
        """Should recommend the next topic to learn."""
        from calculus_rag.prerequisites.detector import GapDetector

        detector = GapDetector(sample_graph)
        completed_topics = {"algebra.basics", "algebra.factoring"}

        next_topic = detector.get_next_topic(
            target_topic="derivatives.chain_rule",
            completed_topics=completed_topics,
        )

        # Should recommend functions.notation (prerequisite that's now learnable)
        assert next_topic == "functions.notation"


class TestGapDetectorIntegration:
    """Integration tests for gap detection."""

    def test_full_gap_analysis(self) -> None:
        """Should perform complete gap analysis for a student query."""
        from calculus_rag.prerequisites.detector import GapDetector, GapAnalysis
        from calculus_rag.prerequisites.graph import PrerequisiteGraph

        # Set up graph
        graph = PrerequisiteGraph()
        graph.add_topic("functions.composition", prerequisites=[])
        graph.add_topic("derivatives.basic", prerequisites=[])
        graph.add_topic("derivatives.chain_rule", prerequisites=["derivatives.basic", "functions.composition"])

        detector = GapDetector(graph)

        # Student has only done basic derivatives
        completed_topics = {"derivatives.basic"}
        query = "How do I find the derivative of sin(x^2)?"

        analysis = detector.analyze(query, completed_topics)

        assert isinstance(analysis, GapAnalysis)
        assert analysis.detected_topic == "derivatives.chain_rule"
        assert len(analysis.missing_prerequisites) > 0
        assert "functions.composition" in analysis.missing_prerequisites
        assert analysis.has_gaps is True
