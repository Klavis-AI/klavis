"""Shared request-scoped context for the emails MCP server.

This module holds the ContextVar and helper functions that tools use to obtain
per-request email configuration and services.  It is intentionally separate
from server.py to avoid circular imports (tools -> server -> tools).
"""

import logging
from contextvars import ContextVar

from .config import config_manager
from .models.config import EmailConfig
from .services import EmailService, FolderService, SearchService, DraftService
from .backends import IMAPBackend, SMTPBackend, FileBackend

logger = logging.getLogger(__name__)

# Context variable to store the email config for each request
email_config_context: ContextVar[EmailConfig] = ContextVar('email_config')


def get_email_config() -> EmailConfig:
    """Get the email configuration from the current request context."""
    try:
        return email_config_context.get()
    except LookupError:
        raise RuntimeError("Email configuration not found in request context")


def parse_email_config_from_dict(data: dict) -> EmailConfig:
    """Parse a dict (from JSON auth data) into an EmailConfig."""
    return EmailConfig(
        email=data.get('email', ''),
        password=data.get('password', ''),
        name=data.get('name', ''),
        imap_server=data.get('imap_server', 'localhost'),
        imap_port=int(data.get('imap_port', 993)),
        smtp_server=data.get('smtp_server', 'localhost'),
        smtp_port=int(data.get('smtp_port', 587)),
        use_ssl=data.get('use_ssl', True),
        use_starttls=data.get('use_starttls', True),
    )


def create_services(email_config: EmailConfig):
    """Create service instances from an EmailConfig (called per-request)."""
    # Create backends
    imap_backend = IMAPBackend(email_config)
    smtp_backend = SMTPBackend(email_config)

    email_export_path = (
        config_manager.workspace_config.email_export_path
        if config_manager.workspace_config
        else None
    )
    attachment_download_path = (
        config_manager.workspace_config.attachment_download_path
        if config_manager.workspace_config
        else None
    )
    file_backend = FileBackend(email_export_path, attachment_download_path)

    # Create services
    email_service = EmailService(email_config)
    folder_service = FolderService(imap_backend)
    search_service = SearchService(imap_backend)
    draft_service = DraftService(file_backend)

    return email_service, folder_service, search_service, draft_service
