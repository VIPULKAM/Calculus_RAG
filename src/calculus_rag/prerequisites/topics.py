"""
Topic catalog for calculus curriculum.

Defines all topics with their metadata, display names, and prerequisites.
"""

from typing import Any

from calculus_rag.prerequisites.graph import PrerequisiteGraph

# Complete calculus curriculum with prerequisites
CALCULUS_TOPICS: dict[str, dict[str, Any]] = {
    # ==========================================================================
    # Pre-Calculus: Algebra
    # ==========================================================================
    "algebra.basics": {
        "display_name": "Algebra Basics",
        "description": "Fundamental algebraic operations and expressions",
        "difficulty": 1,
        "prerequisites": [],
        "tags": ["foundational", "algebra"],
    },
    "algebra.factoring": {
        "display_name": "Factoring",
        "description": "Factoring polynomials and algebraic expressions",
        "difficulty": 2,
        "prerequisites": ["algebra.basics"],
        "tags": ["algebra", "foundational"],
    },
    "algebra.rational_expressions": {
        "display_name": "Rational Expressions",
        "description": "Working with fractions containing polynomials",
        "difficulty": 2,
        "prerequisites": ["algebra.factoring"],
        "tags": ["algebra"],
    },
    "algebra.exponents": {
        "display_name": "Exponent Rules",
        "description": "Laws of exponents and exponential expressions",
        "difficulty": 2,
        "prerequisites": ["algebra.basics"],
        "tags": ["algebra", "foundational"],
    },
    # ==========================================================================
    # Pre-Calculus: Functions
    # ==========================================================================
    "functions.notation": {
        "display_name": "Function Notation",
        "description": "Understanding f(x) notation and function evaluation",
        "difficulty": 1,
        "prerequisites": ["algebra.basics"],
        "tags": ["functions", "foundational"],
    },
    "functions.domain_range": {
        "display_name": "Domain and Range",
        "description": "Finding domain and range of functions",
        "difficulty": 2,
        "prerequisites": ["functions.notation"],
        "tags": ["functions"],
    },
    "functions.composition": {
        "display_name": "Function Composition",
        "description": "Composing functions: f(g(x))",
        "difficulty": 3,
        "prerequisites": ["functions.notation"],
        "tags": ["functions", "important"],
    },
    "functions.inverse": {
        "display_name": "Inverse Functions",
        "description": "Finding and understanding inverse functions",
        "difficulty": 3,
        "prerequisites": ["functions.notation"],
        "tags": ["functions"],
    },
    # ==========================================================================
    # Pre-Calculus: Trigonometry
    # ==========================================================================
    "trig.unit_circle": {
        "display_name": "Unit Circle",
        "description": "Understanding the unit circle and trigonometric values",
        "difficulty": 2,
        "prerequisites": ["algebra.basics"],
        "tags": ["trigonometry", "foundational"],
    },
    "trig.identities": {
        "display_name": "Trigonometric Identities",
        "description": "Common trig identities and their applications",
        "difficulty": 3,
        "prerequisites": ["trig.unit_circle"],
        "tags": ["trigonometry"],
    },
    "trig.inverse": {
        "display_name": "Inverse Trigonometric Functions",
        "description": "Arcsin, arccos, arctan and their properties",
        "difficulty": 3,
        "prerequisites": ["trig.unit_circle", "functions.inverse"],
        "tags": ["trigonometry"],
    },
    # ==========================================================================
    # Pre-Calculus: Exponentials & Logarithms
    # ==========================================================================
    "exp_log.exponentials": {
        "display_name": "Exponential Functions",
        "description": "Properties of exponential functions",
        "difficulty": 2,
        "prerequisites": ["algebra.exponents", "functions.notation"],
        "tags": ["exponentials"],
    },
    "exp_log.logarithms": {
        "display_name": "Logarithms",
        "description": "Logarithmic functions and their properties",
        "difficulty": 3,
        "prerequisites": ["exp_log.exponentials", "functions.inverse"],
        "tags": ["logarithms"],
    },
    # ==========================================================================
    # Calculus: Limits
    # ==========================================================================
    "limits.introduction": {
        "display_name": "Introduction to Limits",
        "description": "Understanding the concept of limits",
        "difficulty": 3,
        "prerequisites": ["algebra.factoring", "functions.notation"],
        "tags": ["limits", "foundational", "calculus"],
    },
    "limits.techniques": {
        "display_name": "Limit Techniques",
        "description": "Direct substitution, factoring, and rationalization",
        "difficulty": 3,
        "prerequisites": ["limits.introduction", "algebra.rational_expressions"],
        "tags": ["limits", "calculus"],
    },
    "limits.infinity": {
        "display_name": "Limits at Infinity",
        "description": "Limits involving infinity",
        "difficulty": 4,
        "prerequisites": ["limits.techniques"],
        "tags": ["limits", "calculus"],
    },
    "limits.continuity": {
        "display_name": "Continuity",
        "description": "Continuous functions and the intermediate value theorem",
        "difficulty": 3,
        "prerequisites": ["limits.introduction"],
        "tags": ["limits", "calculus"],
    },
    # ==========================================================================
    # Calculus: Derivatives
    # ==========================================================================
    "derivatives.definition": {
        "display_name": "Definition of Derivative",
        "description": "Understanding derivatives as limits",
        "difficulty": 3,
        "prerequisites": ["limits.introduction"],
        "tags": ["derivatives", "foundational", "calculus"],
    },
    "derivatives.basic": {
        "display_name": "Basic Derivative Rules",
        "description": "Power rule, constant rule, sum/difference rules",
        "difficulty": 2,
        "prerequisites": ["derivatives.definition"],
        "tags": ["derivatives", "calculus"],
    },
    "derivatives.power_rule": {
        "display_name": "Power Rule",
        "description": "Derivatives of x^n",
        "difficulty": 2,
        "prerequisites": ["derivatives.basic"],
        "tags": ["derivatives", "calculus"],
    },
    "derivatives.product_rule": {
        "display_name": "Product Rule",
        "description": "Derivatives of products of functions",
        "difficulty": 3,
        "prerequisites": ["derivatives.basic"],
        "tags": ["derivatives", "calculus"],
    },
    "derivatives.quotient_rule": {
        "display_name": "Quotient Rule",
        "description": "Derivatives of quotients of functions",
        "difficulty": 3,
        "prerequisites": ["derivatives.basic"],
        "tags": ["derivatives", "calculus"],
    },
    "derivatives.chain_rule": {
        "display_name": "Chain Rule",
        "description": "Derivatives of composite functions",
        "difficulty": 4,
        "prerequisites": ["derivatives.basic", "functions.composition"],
        "tags": ["derivatives", "important", "calculus"],
    },
    "derivatives.trig": {
        "display_name": "Trigonometric Derivatives",
        "description": "Derivatives of sin, cos, tan, etc.",
        "difficulty": 3,
        "prerequisites": ["derivatives.basic", "trig.unit_circle"],
        "tags": ["derivatives", "trigonometry", "calculus"],
    },
    "derivatives.exp_log": {
        "display_name": "Exponential and Logarithmic Derivatives",
        "description": "Derivatives of e^x and ln(x)",
        "difficulty": 3,
        "prerequisites": ["derivatives.basic", "exp_log.logarithms"],
        "tags": ["derivatives", "exponentials", "calculus"],
    },
    # ==========================================================================
    # Calculus: Applications of Derivatives
    # ==========================================================================
    "applications.related_rates": {
        "display_name": "Related Rates",
        "description": "Solving related rates problems",
        "difficulty": 4,
        "prerequisites": ["derivatives.chain_rule"],
        "tags": ["applications", "calculus"],
    },
    "applications.optimization": {
        "display_name": "Optimization",
        "description": "Finding maxima and minima",
        "difficulty": 4,
        "prerequisites": ["derivatives.basic"],
        "tags": ["applications", "calculus"],
    },
    # ==========================================================================
    # Calculus: Integration
    # ==========================================================================
    "integration.introduction": {
        "display_name": "Introduction to Integration",
        "description": "Understanding integrals as antiderivatives",
        "difficulty": 3,
        "prerequisites": ["derivatives.basic"],
        "tags": ["integration", "foundational", "calculus"],
    },
    "integration.basic": {
        "display_name": "Basic Integration Rules",
        "description": "Power rule for integration, constant multiples",
        "difficulty": 3,
        "prerequisites": ["integration.introduction"],
        "tags": ["integration", "calculus"],
    },
    "integration.substitution": {
        "display_name": "U-Substitution",
        "description": "Integration by substitution",
        "difficulty": 4,
        "prerequisites": ["integration.basic", "derivatives.chain_rule"],
        "tags": ["integration", "important", "calculus"],
    },
    "integration.parts": {
        "display_name": "Integration by Parts",
        "description": "Using the integration by parts formula",
        "difficulty": 4,
        "prerequisites": ["integration.basic", "derivatives.product_rule"],
        "tags": ["integration", "calculus"],
    },
    "integration.trig": {
        "display_name": "Trigonometric Integration",
        "description": "Integrals involving trig functions",
        "difficulty": 4,
        "prerequisites": ["integration.basic", "trig.identities"],
        "tags": ["integration", "trigonometry", "calculus"],
    },
}


def get_calculus_topics() -> dict[str, dict[str, Any]]:
    """
    Get the complete calculus topic catalog.

    Returns:
        dict: Dictionary of topic_id -> topic metadata.
    """
    return CALCULUS_TOPICS.copy()


def get_topic_info(topic_id: str) -> dict[str, Any] | None:
    """
    Get information about a specific topic.

    Args:
        topic_id: The topic identifier.

    Returns:
        dict | None: Topic metadata, or None if not found.
    """
    return CALCULUS_TOPICS.get(topic_id)


def get_topics_by_difficulty(difficulty: int) -> list[dict[str, Any]]:
    """
    Get all topics at a specific difficulty level.

    Args:
        difficulty: Difficulty level (1-5).

    Returns:
        list[dict]: List of topic metadata dictionaries.
    """
    return [
        {**topic, "id": topic_id}
        for topic_id, topic in CALCULUS_TOPICS.items()
        if topic["difficulty"] == difficulty
    ]


def search_topics(keyword: str) -> list[dict[str, Any]]:
    """
    Search topics by keyword in display name or description.

    Args:
        keyword: Search keyword.

    Returns:
        list[dict]: List of matching topic metadata dictionaries.
    """
    keyword_lower = keyword.lower()
    results = []

    for topic_id, topic in CALCULUS_TOPICS.items():
        if (
            keyword_lower in topic["display_name"].lower()
            or keyword_lower in topic["description"].lower()
            or keyword_lower in " ".join(topic["tags"]).lower()
        ):
            results.append({**topic, "id": topic_id})

    return results


def build_prerequisite_graph() -> PrerequisiteGraph:
    """
    Build a prerequisite graph from the topic catalog.

    Returns:
        PrerequisiteGraph: Graph with all topics and their prerequisites.
    """
    graph = PrerequisiteGraph()

    for topic_id, topic_data in CALCULUS_TOPICS.items():
        graph.add_topic(topic_id, topic_data["prerequisites"])

    return graph
