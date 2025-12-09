from typing import List, Optional, Tuple
from datetime import datetime
import logging
from ..models.config import EmailConfig
from ..models.email import EmailMessage, SearchResult
from ..backends.imap_backend import IMAPBackend
from ..backends.smtp_backend import SMTPBackend
from ..utils.exceptions import EmailMCPError, ValidationError
from ..utils.validators import validate_page_params, validate_search_query
from ..utils.email_parser import format_email_summary


class EmailService:
    """Email operations service layer"""
    
    def __init__(self, email_config: EmailConfig):
        self.config = email_config
        self.imap_backend = IMAPBackend(email_config)
        self.smtp_backend = SMTPBackend(email_config)
    
    def get_emails(self, folder: str = "INBOX", page: int = 1, page_size: int = 20) -> SearchResult:
        """Get paginated emails from folder"""
        try:
            # Validate parameters
            page, page_size, warning = validate_page_params(page, page_size)
            
            # Get total count and select folder
            total_messages, unread_count = self.imap_backend.select_folder(folder)
            
            if total_messages == 0:
                return SearchResult(
                    emails=[],
                    total_results=0,
                    current_page=1,
                    page_size=page_size,
                    query="",
                    folder=folder
                )
            
            # Calculate pagination
            total_pages = (total_messages + page_size - 1) // page_size
            if page > total_pages:
                page = total_pages
            
            # Get email IDs for current page
            start_idx = (page - 1) * page_size
            email_ids = self.imap_backend.get_email_ids(folder, limit=total_messages)
            page_ids = email_ids[start_idx:start_idx + page_size]
            
            # Fetch emails
            emails = []
            for email_id in page_ids:
                try:
                    email_obj = self.imap_backend.fetch_email(email_id)
                    emails.append(email_obj)
                except Exception as e:
                    # Log error but continue with other emails
                    import logging
                    logging.error(f"Failed to fetch email {email_id}: {str(e)}")
            
            result = SearchResult(
                emails=emails,
                total_results=total_messages,
                current_page=page,
                page_size=page_size,
                query="",
                folder=folder
            )
            
            return result
            
        except Exception as e:
            raise EmailMCPError(f"Failed to get emails: {str(e)}")
    
    def read_email(self, email_id: str) -> EmailMessage:
        """Read specific email by ID"""
        try:
            email_obj = self.imap_backend.fetch_email(email_id)
            
            # Mark as read
            if self.imap_backend.mark_as_read(email_id):
                email_obj.is_read = True
            else:
                logging.warning(f"Failed to mark email {email_id} as read")
                # Continue anyway, as the email content was retrieved successfully
            
            return email_obj
            
        except Exception as e:
            raise EmailMCPError(f"Failed to read email {email_id}: {str(e)}")
    
    def search_emails(self, query: str, folder: Optional[str] = None, 
                     page: int = 1, page_size: int = 20) -> SearchResult:
        """Search emails with pagination"""
        try:
            # Validate query
            valid, error = validate_search_query(query)
            if not valid:
                raise ValidationError(error)
            
            # Validate parameters
            page, page_size, warning = validate_page_params(page, page_size)
            
            # Search emails
            email_ids = self.imap_backend.search_emails(query, folder)
            total_results = len(email_ids)
            
            if total_results == 0:
                return SearchResult(
                    emails=[],
                    total_results=0,
                    current_page=1,
                    page_size=page_size,
                    query=query,
                    folder=folder
                )
            
            # Calculate pagination
            total_pages = (total_results + page_size - 1) // page_size
            if page > total_pages:
                page = total_pages
            
            # Get page slice
            start_idx = (page - 1) * page_size
            page_ids = email_ids[start_idx:start_idx + page_size]
            
            # Fetch emails
            emails = []
            for email_id in page_ids:
                try:
                    email_obj = self.imap_backend.fetch_email(email_id)
                    emails.append(email_obj)
                except Exception as e:
                    import logging
                    logging.error(f"Failed to fetch search result {email_id}: {str(e)}")
            
            return SearchResult(
                emails=emails,
                total_results=total_results,
                current_page=page,
                page_size=page_size,
                query=query,
                folder=folder
            )
            
        except Exception as e:
            raise EmailMCPError(f"Failed to search emails: {str(e)}")
    
    def send_email(self, to: str, subject: str, body: str,
                   html_body: Optional[str] = None,
                   cc: Optional[str] = None,
                   bcc: Optional[str] = None,
                   attachments: Optional[List[str]] = None,
                   save_to_sent: bool = True) -> bool:
        """Send email and optionally save to Sent folder"""
        try:
            # Send the email first
            success, message_string = self.smtp_backend.send_email(
                to=to,
                subject=subject,
                body=body,
                html_body=html_body,
                cc=cc,
                bcc=bcc,
                attachments=attachments
            )
            
            # If sending was successful and save_to_sent is True, save to Sent folder
            if success and save_to_sent and message_string:
                try:
                    # Try common sent folder names
                    sent_folders = ["Sent", "INBOX.Sent", "Sent Messages", "Sent Items"]
                    saved = False
                    
                    for folder in sent_folders:
                        try:
                            self.imap_backend.append_message(folder, message_string)
                            saved = True
                            logging.info(f"Email saved to {folder} folder")
                            break
                        except Exception as e:
                            logging.debug(f"Failed to save to {folder}: {str(e)}")
                            continue
                    
                    if not saved:
                        logging.warning("Could not save email to any Sent folder")
                
                except Exception as e:
                    logging.error(f"Error saving email to Sent folder: {str(e)}")
                    # Don't fail the whole operation if saving to Sent fails
            
            return success
            
        except Exception as e:
            raise EmailMCPError(f"Failed to send email: {str(e)}")
    
    def reply_email(self, email_id: str, body: str,
                   html_body: Optional[str] = None,
                   cc: Optional[str] = None,
                   bcc: Optional[str] = None,
                   reply_all: bool = False) -> bool:
        """Reply to email"""
        try:
            # Get original email
            original_email = self.imap_backend.fetch_email(email_id)
            
            # Prepare reply subject
            original_subject = original_email.subject or ""
            reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
            
            # Determine recipients
            reply_to = original_email.from_addr
            
            if reply_all:
                # Include original TO and CC recipients (excluding ourselves)
                all_recipients = []
                if original_email.to_addr:
                    all_recipients.extend([addr.strip() for addr in original_email.to_addr.split(',')])
                if original_email.cc_addr:
                    all_recipients.extend([addr.strip() for addr in original_email.cc_addr.split(',')])
                
                # Remove our own email (handle both "email" and "Name <email>" formats)
                our_email = self.config.email.lower()
                all_recipients = [addr for addr in all_recipients 
                                if our_email not in addr.lower()]
                reply_cc = ','.join(all_recipients) if all_recipients else cc
            else:
                reply_cc = cc
            
            # Prepare body with original message
            original_body = original_email.body_text or ""
            full_body = f"{body}\n\n--- Original Message ---\nFrom: {original_email.from_addr}\nDate: {original_email.date}\nSubject: {original_subject}\n\n{original_body}"
            
            # Prepare HTML body if provided
            full_html_body = None
            if html_body:
                original_html = original_email.body_html or original_body
                full_html_body = f"{html_body}<br><br><hr><b>Original Message:</b><br>From: {original_email.from_addr}<br>Date: {original_email.date}<br>Subject: {original_subject}<br><br>{original_html}"
            
            # Send reply
            return self.send_email(
                to=reply_to,
                subject=reply_subject,
                body=full_body,
                html_body=full_html_body,
                cc=reply_cc,
                bcc=bcc
            )
            
        except Exception as e:
            raise EmailMCPError(f"Failed to reply to email: {str(e)}")
    
    def forward_email(self, email_id: str, to: str,
                     body: Optional[str] = None,
                     html_body: Optional[str] = None,
                     cc: Optional[str] = None,
                     bcc: Optional[str] = None) -> bool:
        """Forward email with attachments"""
        try:
            # Get original email
            original_email = self.imap_backend.fetch_email(email_id)
            
            # Prepare forward subject
            original_subject = original_email.subject or ""
            forward_subject = f"Fwd: {original_subject}" if not original_subject.startswith('Fwd:') else original_subject
            
            # Prepare body with forwarded content
            original_body = original_email.body_text or ""
            forward_body = f"{body or ''}\n\n--- Forwarded Message ---\nFrom: {original_email.from_addr}\nTo: {original_email.to_addr}\nDate: {original_email.date}\nSubject: {original_subject}\n\n{original_body}"
            
            # Prepare HTML body if provided
            forward_html_body = None
            if html_body or original_email.body_html:
                original_html = original_email.body_html or original_body
                forward_html_body = f"{html_body or ''}<br><br><hr><b>Forwarded Message:</b><br>From: {original_email.from_addr}<br>To: {original_email.to_addr}<br>Date: {original_email.date}<br>Subject: {original_subject}<br><br>{original_html}"
            
            # Forward with attachments from the original email
            return self._send_with_original_attachments(
                to=to,
                subject=forward_subject,
                body=forward_body,
                html_body=forward_html_body,
                cc=cc,
                bcc=bcc,
                original_email=original_email
            )
            
        except Exception as e:
            raise EmailMCPError(f"Failed to forward email: {str(e)}")
    
    def _send_with_original_attachments(self, to: str, subject: str, body: str,
                                      html_body: Optional[str] = None,
                                      cc: Optional[str] = None,
                                      bcc: Optional[str] = None,
                                      original_email: EmailMessage = None) -> bool:
        """Send email with attachments from original email"""
        try:
            if not original_email or not original_email.attachments:
                # No attachments, use regular send_email
                return self.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    cc=cc,
                    bcc=bcc
                )
            
            # Extract attachment data from original email's raw message
            import tempfile
            import os
            temp_files = []
            
            try:
                if original_email.raw_message:
                    for part in original_email.raw_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            if filename:
                                # Decode attachment data
                                attachment_data = part.get_payload(decode=True)
                                if attachment_data:
                                    # Create temporary file with original filename
                                    import tempfile
                                    temp_dir = tempfile.mkdtemp()
                                    temp_file_path = os.path.join(temp_dir, filename)
                                    with open(temp_file_path, 'wb') as f:
                                        f.write(attachment_data)
                                    temp_files.append(temp_file_path)
                
                # Send email with temporary attachment files
                success = self.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    cc=cc,
                    bcc=bcc,
                    attachments=temp_files
                )
                
                return success
                
            finally:
                # Clean up temporary files and directories
                for temp_file_path in temp_files:
                    try:
                        os.unlink(temp_file_path)
                        # Also remove the temporary directory if it's empty
                        temp_dir = os.path.dirname(temp_file_path)
                        try:
                            os.rmdir(temp_dir)
                        except OSError:
                            pass  # Directory not empty or already removed
                    except:
                        pass
            
        except Exception as e:
            raise EmailMCPError(f"Failed to send email with original attachments: {str(e)}")
    
    def _check_email_exists(self, email_id: str) -> bool:
        """Check if email exists in current folder"""
        try:
            # Try to fetch just the flags to check existence
            status, data = self.imap_backend.connection.fetch(email_id, '(FLAGS)')
            return status == 'OK' and data and len(data) > 0
        except Exception:
            return False
    
    def delete_email(self, email_id: str) -> bool:
        """Delete email"""
        try:
            self.imap_backend.delete_email(email_id)
            return True
        except Exception as e:
            raise EmailMCPError(f"Failed to delete email: {str(e)}")
    
    def move_email(self, email_id: str, target_folder: str) -> bool:
        """Move email to another folder"""
        try:
            self.imap_backend.move_email(email_id, target_folder)
            return True
        except Exception as e:
            raise EmailMCPError(f"Failed to move email: {str(e)}")
    
    def mark_emails(self, email_ids: List[str], status: str) -> int:
        """Mark multiple emails with status (read/unread/important)"""
        success_count = 0
        
        for email_id in email_ids:
            try:
                success = False
                if status == "read":
                    success = self.imap_backend.mark_as_read(email_id)
                elif status == "unread":
                    success = self.imap_backend.mark_as_unread(email_id)
                elif status == "important":
                    success = self.imap_backend.mark_as_important(email_id)
                elif status == "not_important":
                    success = self.imap_backend.mark_as_not_important(email_id)
                
                if success:
                    success_count += 1
                else:
                    logging.warning(f"Failed to mark email {email_id} as {status}")
            except Exception as e:
                logging.error(f"Failed to mark email {email_id} as {status}: {str(e)}")
        
        return success_count
    
    def check_connection(self) -> Tuple[bool, bool]:
        """Check IMAP and SMTP connections"""
        imap_ok = False
        smtp_ok = False
        
        try:
            self.imap_backend.ensure_connected()
            imap_ok = True
        except:
            pass
        
        try:
            smtp_ok = self.smtp_backend.test_connection()
        except:
            pass
        
        return imap_ok, smtp_ok
    
    def cleanup(self):
        """Cleanup connections"""
        self.imap_backend.disconnect()
        self.smtp_backend.disconnect()