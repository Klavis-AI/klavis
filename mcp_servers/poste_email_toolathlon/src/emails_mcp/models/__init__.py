from .config import EmailConfig, WorkspaceConfig
from .email import EmailMessage, EmailAttachment, EmailFolder, SearchResult, MailboxStats

__all__ = [
    'EmailConfig',
    'WorkspaceConfig', 
    'EmailMessage',
    'EmailAttachment',
    'EmailFolder',
    'SearchResult',
    'MailboxStats'
]