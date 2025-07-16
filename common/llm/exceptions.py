#!/usr/bin/env python3
"""
LLM-related exceptions for AI Agent System
"""


class LLMError(Exception):
    """Base exception for LLM-related errors"""
    
    def __init__(self, message: str, provider: str = None, error_code: str = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code


class LLMTimeoutError(LLMError):
    """Exception raised when LLM request times out"""
    pass


class LLMRateLimitError(LLMError):
    """Exception raised when LLM rate limit is exceeded"""
    
    def __init__(self, message: str, provider: str = None, retry_after: int = None):
        super().__init__(message, provider)
        self.retry_after = retry_after


class LLMAuthenticationError(LLMError):
    """Exception raised when LLM authentication fails"""
    pass


class LLMQuotaExceededError(LLMError):
    """Exception raised when LLM quota is exceeded"""
    pass


class LLMModelNotFoundError(LLMError):
    """Exception raised when requested LLM model is not found"""
    pass


class LLMInvalidRequestError(LLMError):
    """Exception raised when LLM request is invalid"""
    pass