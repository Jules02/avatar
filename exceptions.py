"""Custom exceptions for the Avatar application."""
from typing import Optional, Dict, Any


class AvatarError(Exception):
    """Base exception for all Avatar-specific exceptions."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(AvatarError):
    """Raised when there's an error in the application configuration."""
    pass


class AuthenticationError(AvatarError):
    """Raised when there's an authentication error with an external service."""
    pass


class ServiceError(AvatarError):
    """Raised when there's an error with an external service."""
    pass


class ValidationError(AvatarError):
    """Raised when input validation fails."""
    pass


class KimbleError(ServiceError):
    """Raised when there's an error with the Kimble service."""
    pass


def handle_error(error: Exception) -> None:
    """Handle errors consistently across the application.
    
    Args:
        error: The exception to handle
        
    Raises:
        The original error if it's not one of our custom exceptions
    """
    from loguru import logger
    
    if isinstance(error, AvatarError):
        logger.error(f"{error.__class__.__name__}: {error.message}", **error.details)
    else:
        logger.opt(exception=error).error("Unexpected error occurred")
    
    # Re-raise the error to be handled by the caller
    raise error
