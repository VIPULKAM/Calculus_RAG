"""
Prerequisite gap detection.

Analyzes student queries and completed topics to identify knowledge gaps
and suggest learning paths.
"""

from dataclasses import dataclass

from calculus_rag.prerequisites.graph import PrerequisiteGraph


@dataclass
class GapAnalysis:
    """
    Result of gap detection analysis.

    Attributes:
        detected_topic: The topic detected from the query.
        missing_prerequisites: List of prerequisite topics not yet completed.
        has_gaps: Whether there are any missing prerequisites.
        next_topic: Suggested next topic to learn.
        suggestions: List of learning suggestions.
    """

    detected_topic: str | None
    missing_prerequisites: list[str]
    has_gaps: bool
    next_topic: str | None = None
    suggestions: list[str] | None = None


class GapDetector:
    """
    Detects prerequisite gaps in student knowledge.

    Uses the prerequisite graph and student completion history to:
    - Identify missing prerequisites
    - Detect confusion signals
    - Suggest learning paths
    """

    # Keywords for detecting topics in queries
    TOPIC_KEYWORDS = {
        "limits.introduction": ["limit", "limits", "approaches", "approaching"],
        "derivatives.basic": ["derivative", "differentiate", "differentiation", "rate of change"],
        "derivatives.chain_rule": ["chain rule", "composite", "nested function", "sin(x^2)", "cos(x^2)"],
        "derivatives.product_rule": ["product rule", "multiply", "product"],
        "derivatives.quotient_rule": ["quotient rule", "divide", "fraction"],
        "integration.basic": ["integral", "integrate", "integration", "antiderivative"],
        "integration.substitution": ["u-substitution", "substitution", "u sub"],
        "functions.composition": ["composition", "composite", "f(g(x))", "nested"],
        "algebra.factoring": ["factor", "factoring", "factorize"],
    }

    # Confusion signal phrases
    CONFUSION_SIGNALS = [
        "don't understand",
        "confused",
        "what is",
        "what are",
        "explain",
        "help me understand",
        "not sure",
        "unclear",
        "can you explain",
    ]

    def __init__(self, prerequisite_graph: PrerequisiteGraph) -> None:
        """
        Initialize the gap detector.

        Args:
            prerequisite_graph: The prerequisite graph to use.
        """
        self.graph = prerequisite_graph

    def detect_gaps(self, topic: str, completed_topics: set[str]) -> list[str]:
        """
        Detect prerequisite gaps for a topic.

        Args:
            topic: The target topic.
            completed_topics: Set of topics the student has completed.

        Returns:
            list[str]: List of missing prerequisite topics.
        """
        return self.graph.get_missing_prerequisites(topic, completed_topics)

    def detect_critical_gaps(self, topic: str, completed_topics: set[str]) -> list[str]:
        """
        Detect critical gaps (foundational prerequisites).

        Critical gaps are topics that have no prerequisites themselves
        but are required for the target topic.

        Args:
            topic: The target topic.
            completed_topics: Set of topics the student has completed.

        Returns:
            list[str]: List of critical prerequisite topics to address first.
        """
        all_gaps = self.detect_gaps(topic, completed_topics)

        # Filter to only foundational topics (those with no prerequisites)
        critical = []
        for gap in all_gaps:
            prereqs = self.graph.get_prerequisites(gap)
            if not prereqs:
                critical.append(gap)

        return critical

    def analyze_query(self, query: str) -> str | None:
        """
        Analyze a query to detect which topic is being asked about.

        Args:
            query: The student's query.

        Returns:
            str | None: Detected topic identifier, or None if not detected.
        """
        query_lower = query.lower()

        # Check for chain rule patterns first (more specific)
        if any(pattern in query_lower for pattern in ["sin(x^2)", "cos(x^2)", "chain", "composite", "nested"]):
            return "derivatives.chain_rule"

        # Then check for topic keywords
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    return topic

        # Fallback to general patterns
        if "limit" in query_lower:
            return "limits.introduction"
        elif "derivative" in query_lower:
            return "derivatives.basic"
        elif "integral" in query_lower:
            return "integration.basic"

        return None

    def has_confusion_signals(self, query: str) -> bool:
        """
        Check if query contains confusion signals.

        Args:
            query: The student's query.

        Returns:
            bool: True if confusion signals detected.
        """
        query_lower = query.lower()

        for signal in self.CONFUSION_SIGNALS:
            if signal in query_lower:
                return True

        return False

    def suggest_review(self, target_topic: str, completed_topics: set[str]) -> list[str]:
        """
        Suggest which topics to review before learning the target topic.

        Args:
            target_topic: The topic the student wants to learn.
            completed_topics: Topics the student has completed.

        Returns:
            list[str]: List of suggestion strings.
        """
        gaps = self.detect_gaps(target_topic, completed_topics)

        if not gaps:
            return []

        suggestions = []

        # Get critical gaps (foundational)
        critical = self.detect_critical_gaps(target_topic, completed_topics)

        if critical:
            suggestions.append(
                f"Before learning {target_topic}, let's review these foundational concepts: "
                + ", ".join(critical)
            )

        # Suggest next immediate prerequisite
        next_topic = self.get_next_topic(target_topic, completed_topics)
        if next_topic:
            suggestions.append(
                f"The next topic you should learn is: {next_topic}"
            )

        return suggestions

    def get_next_topic(self, target_topic: str, completed_topics: set[str]) -> str | None:
        """
        Get the next topic the student should learn to progress toward target.

        Args:
            target_topic: The ultimate topic to learn.
            completed_topics: Topics already completed.

        Returns:
            str | None: The next topic to learn, or None if ready for target.
        """
        gaps = self.detect_gaps(target_topic, completed_topics)

        if not gaps:
            return None

        # Get learning path
        path = self.graph.get_learning_path(target_topic, completed_topics)

        # Return first item in path (the next thing to learn)
        return path[0] if path else None

    def analyze(self, query: str, completed_topics: set[str]) -> GapAnalysis:
        """
        Perform complete gap analysis for a student query.

        Args:
            query: The student's query.
            completed_topics: Topics the student has completed.

        Returns:
            GapAnalysis: Complete analysis with gaps and suggestions.
        """
        # Detect topic from query
        detected_topic = self.analyze_query(query)

        if not detected_topic:
            # Cannot analyze without knowing the topic
            return GapAnalysis(
                detected_topic=None,
                missing_prerequisites=[],
                has_gaps=False,
                suggestions=["Unable to detect the topic from your query. Could you be more specific?"],
            )

        # Detect gaps
        missing = self.detect_gaps(detected_topic, completed_topics)
        has_gaps = len(missing) > 0

        # Get next topic
        next_topic = self.get_next_topic(detected_topic, completed_topics)

        # Generate suggestions
        suggestions = self.suggest_review(detected_topic, completed_topics)

        return GapAnalysis(
            detected_topic=detected_topic,
            missing_prerequisites=missing,
            has_gaps=has_gaps,
            next_topic=next_topic,
            suggestions=suggestions if suggestions else None,
        )

    def __repr__(self) -> str:
        return f"GapDetector(topics={len(self.graph.get_all_topics())})"
