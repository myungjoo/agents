"""
Issue Detector Agent

Detects correctness bugs, memory bugs, and performance issues
in source code using static analysis and LLM-based analysis.
"""

from .agent import IssueDetector

__all__ = ['IssueDetector']