import re
from typing import Optional
from pathlib import Path
from .exceptions import ValidationError


def validate_email_address(email: str) -> bool:
    """Validate email address format with international domain support"""
    if not email or not isinstance(email, str):
        return False
    
    # More flexible pattern that supports international domains
    # Split into local and domain parts for separate validation
    if '@' not in email:
        return False
    
    local_part, domain_part = email.rsplit('@', 1)
    
    # Validate local part (before @)
    # Allow ASCII characters and common symbols, but not international characters in local part
    # This follows RFC 5321 more closely
    if not local_part or len(local_part) > 64:
        return False
    
    # Check for valid characters in local part (ASCII only for now)
    # Allow letters, numbers, and common symbols
    valid_local_chars = re.match(r'^[a-zA-Z0-9._%+-]+$', local_part)
    if not valid_local_chars:
        return False
    
    # Basic validation: no consecutive dots, no start/end with dot
    if local_part.startswith('.') or local_part.endswith('.') or '..' in local_part:
        return False
    
    # Validate domain part (after @)
    if not domain_part or len(domain_part) > 255:
        return False
    
    # Domain should have at least one dot and valid structure
    if '.' not in domain_part:
        return False
    
    # Split domain into parts
    domain_parts = domain_part.split('.')
    if len(domain_parts) < 2:
        return False
    
    # Each domain part should not be empty and should have reasonable length
    for part in domain_parts:
        if not part or len(part) > 63:
            return False
        # Allow international characters in domain names (IDN support)
        if not re.match(r'^[a-zA-Z0-9\u00a1-\uffff-]+$', part):
            return False
    
    # TLD should be at least 2 characters (but allow international TLDs)
    if len(domain_parts[-1]) < 2:
        return False
    
    return True


def validate_email_list(email_list: str) -> tuple[bool, str]:
    """Validate comma-separated email list"""
    if not email_list:
        return False, "Email list cannot be empty"
    
    emails = [email.strip() for email in email_list.split(',')]
    invalid_emails = []
    
    for email in emails:
        if not validate_email_address(email):
            invalid_emails.append(email)
    
    if invalid_emails:
        return False, f"Invalid email addresses: {', '.join(invalid_emails)}"
    
    return True, ""


def validate_page_params(page: int, page_size: int, max_page_size: int = 50) -> tuple[int, int, str]:
    """Validate and normalize pagination parameters"""
    warning = ""
    
    if page < 1:
        page = 1
        warning += "Page number adjusted to 1. "
    
    if page_size < 1:
        page_size = 20
        warning += "Page size adjusted to 20. "
    elif page_size > max_page_size:
        page_size = max_page_size
        warning += f"Page size limited to {max_page_size}. "
    
    return page, page_size, warning


def validate_file_path(file_path: str, must_exist: bool = True) -> tuple[bool, str]:
    """Validate file path"""
    if not file_path:
        return False, "File path cannot be empty"
    
    try:
        path = Path(file_path)
        
        if must_exist and not path.exists():
            return False, f"File does not exist: {file_path}"
        
        if must_exist and not path.is_file():
            return False, f"Path is not a file: {file_path}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Invalid file path: {str(e)}"


def validate_folder_name(folder_name: str) -> tuple[bool, str]:
    """Validate email folder name"""
    if not folder_name:
        return False, "Folder name cannot be empty"
    
    # Basic validation - no path separators or special chars
    invalid_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in folder_name:
            return False, f"Folder name contains invalid character: {char}"
    
    if len(folder_name) > 255:
        return False, "Folder name too long (max 255 characters)"
    
    return True, ""


def sanitize_subject(subject: str) -> str:
    """Sanitize email subject"""
    if not subject:
        return ""
    
    # Remove control characters and normalize whitespace
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', subject)
    sanitized = ' '.join(sanitized.split())
    
    return sanitized[:998]  # RFC limit for subject length


def validate_search_query(query: str) -> tuple[bool, str]:
    """Validate search query"""
    if not query or not query.strip():
        return False, "Search query cannot be empty"
    
    if len(query) > 1000:
        return False, "Search query too long (max 1000 characters)"
    
    return True, ""