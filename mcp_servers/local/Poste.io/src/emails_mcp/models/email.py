from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class EmailAttachment:
    """Email attachment information"""
    filename: str
    content_type: str
    size: int
    attachment_id: Optional[str] = None
    content: Optional[bytes] = None  # 附件的实际内容数据


@dataclass
class EmailMessage:
    """Email message data model"""
    email_id: str
    subject: str
    from_addr: str
    to_addr: str
    cc_addr: Optional[str] = None
    bcc_addr: Optional[str] = None
    date: Optional[str] = None
    message_id: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = None
    is_read: bool = False
    is_important: bool = False
    folder: Optional[str] = None
    raw_message: Optional[Any] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class EmailFolder:
    """Email folder information"""
    name: str
    total_messages: int = 0
    unread_messages: int = 0
    can_select: bool = True


@dataclass
class SearchResult:
    """Email search result"""
    emails: List[EmailMessage]
    total_results: int
    current_page: int
    page_size: int
    query: str
    folder: Optional[str] = None
    
    @property
    def total_pages(self) -> int:
        return (self.total_results + self.page_size - 1) // self.page_size


@dataclass
class MailboxStats:
    """Mailbox statistics"""
    folder_name: str
    total_messages: int
    unread_messages: int
    total_size_mb: Optional[float] = None