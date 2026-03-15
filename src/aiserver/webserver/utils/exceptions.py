"""Custom exceptions for the web server"""

class FaceRecognitionError(Exception):
    """Exception raised when face recognition processing fails"""
    pass


class FileValidationError(Exception):
    """Exception raised when file validation fails"""
    pass


class ServiceUnavailableError(Exception):
    """Exception raised when a required service is unavailable"""
    pass


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid"""
    pass