class EmailMCPError(Exception):
    """Base exception for Email MCP operations"""
    pass


class ConnectionError(EmailMCPError):
    """Email server connection error"""
    pass


class AuthenticationError(EmailMCPError):
    """Email authentication error"""
    pass


class ConfigurationError(EmailMCPError):
    """Configuration error"""
    pass


class ValidationError(EmailMCPError):
    """Data validation error"""
    pass


class FolderError(EmailMCPError):
    """Email folder operation error"""
    pass


class EmailNotFoundError(EmailMCPError):
    """Email not found error"""
    pass


class AttachmentError(EmailMCPError):
    """Attachment operation error"""
    pass


class SendEmailError(EmailMCPError):
    """Email sending error"""
    pass