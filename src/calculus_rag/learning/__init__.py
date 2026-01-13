"""
Learning module for self-improving RAG.

Allows the system to learn from LLM responses when user confirms
they are correct, adding them to the knowledge base for future use.
"""

from calculus_rag.learning.learner import KnowledgeLearner

__all__ = ["KnowledgeLearner"]
