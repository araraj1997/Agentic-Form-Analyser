"""
QA Module

Provides question answering capabilities for forms.
"""

from src.qa.qa_engine import QAEngine, QueryResult
from src.qa.retriever import ContextRetriever, RetrievalResult

__all__ = ['QAEngine', 'QueryResult', 'ContextRetriever', 'RetrievalResult']
