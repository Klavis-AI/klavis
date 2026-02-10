import email
import email.message
import logging
from email.header import decode_header
from email.utils import parseaddr, formataddr
from typing import Dict, Any, List, Optional
from ..models.email import EmailMessage, EmailAttachment
from .exceptions import ValidationError


def decode_email_header(header_value: str) -> str:
    """Decode email header properly handling encoding with improved Chinese support"""
    if header_value is None:
        return ""
    
    try:
        decoded_parts = decode_header(header_value)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        # Try the specified encoding first
                        result += part.decode(encoding)
                    except (UnicodeDecodeError, LookupError):
                        # Fallback to common Chinese encodings
                        for fallback_encoding in ['utf-8', 'gb2312', 'gbk', 'big5']:
                            try:
                                result += part.decode(fallback_encoding)
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        else:
                            # Final fallback with replacement characters
                            result += part.decode('utf-8', errors='replace')
                else:
                    # No encoding specified, try UTF-8 first, then fallbacks
                    try:
                        result += part.decode('utf-8')
                    except UnicodeDecodeError:
                        for fallback_encoding in ['gb2312', 'gbk', 'big5', 'iso-8859-1']:
                            try:
                                result += part.decode(fallback_encoding)
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        else:
                            result += part.decode('utf-8', errors='replace')
            else:
                result += str(part)
        return result.strip()
    except Exception as e:
        logging.warning(f"Failed to decode header: {str(e)}")
        return str(header_value)


def parse_email_address_with_name(addr_string: str) -> tuple[str, str]:
    """Parse email address with Chinese display name support
    
    Returns:
        tuple[str, str]: (display_name, email_address)
    """
    if not addr_string:
        return "", ""
    
    try:
        # First decode the header to handle Chinese names
        decoded_addr = decode_email_header(addr_string)
        
        # Parse the address
        display_name, email_addr = parseaddr(decoded_addr)
        
        # Clean up the display name and email
        display_name = display_name.strip().strip('"').strip("'")
        email_addr = email_addr.strip()
        
        return display_name, email_addr
    except Exception as e:
        logging.warning(f"Failed to parse email address '{addr_string}': {str(e)}")
        return "", addr_string.strip()


def parse_email_addresses(addr_string: str) -> List[str]:
    """Parse comma-separated email addresses with improved Chinese support"""
    if not addr_string:
        return []
    
    addresses = []
    # Split by comma but be careful about commas in quoted names
    parts = []
    current_part = ""
    in_quotes = False
    bracket_depth = 0
    
    for char in addr_string:
        if char == '"' and bracket_depth == 0:
            in_quotes = not in_quotes
        elif char == '<' and not in_quotes:
            bracket_depth += 1
        elif char == '>' and not in_quotes:
            bracket_depth -= 1
        elif char == ',' and not in_quotes and bracket_depth == 0:
            parts.append(current_part.strip())
            current_part = ""
            continue
        current_part += char
    
    if current_part.strip():
        parts.append(current_part.strip())
    
    for addr in parts:
        if addr:
            # Extract just the email part if in "Name <email>" format
            display_name, email_addr = parse_email_address_with_name(addr)
            if email_addr:
                addresses.append(email_addr)
    
    return addresses


def extract_attachments_info(msg: email.message.Message) -> List[EmailAttachment]:
    """Extract attachment information from email message"""
    attachments = []
    
    if not msg.is_multipart():
        return attachments
    
    for part in msg.walk():
        disposition = part.get('Content-Disposition', '')
        if 'attachment' in disposition:
            filename = part.get_filename()
            if filename:
                # Decode filename if needed
                filename = decode_email_header(filename)
                
                # Get content info
                content_type = part.get_content_type()
                # logging.debug(f"Filename: {filename}")
                # logging.debug(f"Content type: {content_type}")
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0
                
                # logging.debug(f"Payload: {payload}")
                # logging.debug(f"Size: {size}")
                
                attachment = EmailAttachment(
                    filename=filename,
                    content_type=content_type,
                    size=size,
                    content=payload  # 保存附件的实际内容
                )
                attachments.append(attachment)
    
    return attachments


def detect_and_decode_content(payload: bytes, part: email.message.Message) -> str:
    """Detect encoding and decode content with Chinese support"""
    if not payload:
        return ""
    
    # Get charset from content type
    charset = part.get_content_charset()
    
    # Try the specified charset first
    if charset:
        try:
            return payload.decode(charset)
        except (UnicodeDecodeError, LookupError):
            logging.debug(f"Failed to decode with specified charset: {charset}")
    
    # Try common encodings in order of preference
    encodings_to_try = [
        'utf-8',
        'gb2312', 
        'gbk',
        'big5',
        'iso-8859-1',
        'windows-1252'
    ]
    
    for encoding in encodings_to_try:
        try:
            return payload.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Final fallback with replacement characters
    return payload.decode('utf-8', errors='replace')


def extract_email_body(msg: email.message.Message) -> tuple[str, str]:
    """Extract text and HTML body from email message with improved Chinese encoding support"""
    body_text = ""
    body_html = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get('Content-Disposition', '')
            
            # Skip attachments
            if 'attachment' in disposition:
                continue
                
            payload = part.get_payload(decode=True)
            if not payload:
                continue
                
            try:
                content = detect_and_decode_content(payload, part)
            except Exception as e:
                logging.warning(f"Failed to decode email content: {str(e)}")
                continue
                
            if content_type == 'text/plain' and not body_text:
                body_text = content
            elif content_type == 'text/html' and not body_html:
                body_html = content
    else:
        # Single part message
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                content = detect_and_decode_content(payload, msg)
                if msg.get_content_type() == 'text/html':
                    body_html = content
                else:
                    body_text = content
            except Exception as e:
                logging.warning(f"Failed to decode single part message: {str(e)}")
    
    return body_text, body_html


def parse_raw_email(raw_email: bytes, email_id: str) -> EmailMessage:
    """Parse raw email bytes into EmailMessage object with improved Chinese support"""
    try:
        msg = email.message_from_bytes(raw_email)
        
        # Extract headers with proper Chinese decoding
        subject = decode_email_header(msg.get('Subject', ''))
        
        # Parse addresses with Chinese display name support
        from_display_name, from_addr = parse_email_address_with_name(msg.get('From', ''))
        to_display_name, to_addr = parse_email_address_with_name(msg.get('To', ''))
        cc_addr = decode_email_header(msg.get('Cc', '')) or None
        
        # Store the original from address with display name for reply functionality
        original_from = decode_email_header(msg.get('From', ''))
        
        date = msg.get('Date', '')
        message_id = msg.get('Message-ID', '')
        
        # Extract body content with improved encoding detection
        body_text, body_html = extract_email_body(msg)
        
        # Extract attachments
        attachments = extract_attachments_info(msg)
        
        # Create EmailMessage with additional metadata
        email_msg = EmailMessage(
            email_id=email_id,
            subject=subject,
            from_addr=from_addr,
            to_addr=to_addr,
            cc_addr=cc_addr,
            date=date,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            message_id=message_id
        )
        
        # Store the raw message for attachment extraction
        email_msg.raw_message = msg
        
        # Add extra metadata for Chinese support
        if hasattr(email_msg, '__dict__'):
            email_msg.__dict__['from_display_name'] = from_display_name
            email_msg.__dict__['to_display_name'] = to_display_name  
            email_msg.__dict__['original_from'] = original_from
        
        return email_msg
        
    except Exception as e:
        logging.error(f"Failed to parse email {email_id}: {str(e)}")
        raise ValidationError(f"Failed to parse email: {str(e)}")


def format_email_summary(email: EmailMessage, include_body_preview: bool = False) -> str:
    """Format email for display summary"""
    result = f"Subject: {email.subject}\n"
    result += f"From: {email.from_addr}\n"
    result += f"To: {email.to_addr}\n"
    
    if email.cc_addr:
        result += f"CC: {email.cc_addr}\n"
    
    result += f"Date: {email.date}\n"
    
    if email.attachments:
        result += f"Attachments: {len(email.attachments)} files\n"
    
    if include_body_preview and email.body_text:
        preview = email.body_text[:200] + "..." if len(email.body_text) > 200 else email.body_text
        result += f"Preview: {preview}\n"
    
    return result