from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class EmailConfig:
    """Email server configuration"""
    email: str
    password: str
    name: str = ""
    imap_server: str = "localhost"
    imap_port: int = 993
    smtp_server: str = "localhost" 
    smtp_port: int = 587
    use_ssl: bool = True
    use_starttls: bool = True


@dataclass
class WorkspaceConfig:
    """Workspace configuration"""
    attachment_upload_path: Optional[str] = None      # Path for uploading attachments
    attachment_download_path: Optional[str] = None    # Path for downloading attachments  
    email_export_path: Optional[str] = None           # Path for exporting emails
    config_file: Optional[str] = None
    max_page_size: int = 50
    default_page_size: int = 20
    connection_timeout: int = 30
    cache_timeout_minutes: int = 30