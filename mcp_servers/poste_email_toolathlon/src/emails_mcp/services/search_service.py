import logging
from typing import List, Optional
from ..models.email import EmailMessage
from ..backends.imap_backend import IMAPBackend
from ..backends.file_backend import FileBackend
from ..utils.exceptions import EmailMCPError


class SearchService:
    """Email search service layer"""
    
    def __init__(self, imap_backend: IMAPBackend):
        self.imap_backend = imap_backend
    
    def search_emails_by_query(self, query: str, folder: Optional[str] = None) -> List[str]:
        """Search emails and return email IDs"""
        try:
            # If no folder specified, use INBOX as default
            if not folder:
                folder = 'INBOX'
            return self.imap_backend.search_emails(query, folder)
        except Exception as e:
            raise EmailMCPError(f"Failed to search emails: {str(e)}")
    
    def search_by_sender(self, sender: str, folder: Optional[str] = None) -> List[str]:
        """Search emails by sender"""
        try:
            # If no folder specified, use INBOX as default
            if not folder:
                folder = 'INBOX'
            
            # Always select folder before searching
            self.imap_backend.select_folder(folder)
            
            self.imap_backend.ensure_connected()
            
            # Use UTF-8 aware search similar to the main search method
            # Encode sender to UTF-8 bytes for proper Chinese character handling
            sender_bytes = sender.encode('utf-8')
            
            if self.imap_backend.utf8_enabled:
                # When UTF-8 is enabled, don't specify charset
                search_criteria = b'FROM "' + sender_bytes + b'"'
                status, email_ids = self.imap_backend.connection.search(None, search_criteria)
            else:
                # Try UTF-8 charset first
                try:
                    search_criteria = b'FROM "' + sender_bytes + b'"'
                    status, email_ids = self.imap_backend.connection.search('UTF-8', search_criteria)
                except Exception as search_error:
                    logging.warning(f"UTF-8 charset search failed: {search_error}")
                    status = 'NO'
                
                # Improved fallback strategy for Chinese content
                if status != 'OK':
                    # Try different search approaches for Chinese content
                    search_attempts = [
                        # Try searching with quoted sender name only (no special chars)
                        f'FROM "{sender}"',
                        # Try without quotes
                        f'FROM {sender}',
                        # Try with partial email if contains @
                        f'FROM "{sender.split("@")[0]}"' if '@' in sender else None,
                        # Try domain search if email
                        f'FROM "@{sender.split("@")[1]}"' if '@' in sender else None
                    ]
                    
                    for attempt in search_attempts:
                        if attempt is None:
                            continue
                        try:
                            status, email_ids = self.imap_backend.connection.search(None, attempt)
                            if status == 'OK' and email_ids[0]:
                                break
                        except:
                            continue
                    
                    # Final ASCII fallback only if all above failed
                    if status != 'OK':
                        ascii_sender = sender.encode('ascii', errors='ignore').decode('ascii')
                        if ascii_sender.strip():
                            status, email_ids = self.imap_backend.connection.search(None, f'FROM "{ascii_sender}"')
                        else:
                            # Return empty if we can't search at all
                            return []
            
            if status != 'OK':
                raise EmailMCPError(f"Search failed: {status}")
            
            id_list = email_ids[0].split()
            return [uid.decode() for uid in reversed(id_list)]
            
        except Exception as e:
            raise EmailMCPError(f"Failed to search by sender: {str(e)}")
    
    def search_by_subject(self, subject: str, folder: Optional[str] = None) -> List[str]:
        """Search emails by subject"""
        try:
            # If no folder specified, use INBOX as default
            if not folder:
                folder = 'INBOX'
            
            # Always select folder before searching
            self.imap_backend.select_folder(folder)
            
            self.imap_backend.ensure_connected()
            
            # Use UTF-8 aware search similar to the main search method
            # Encode subject to UTF-8 bytes for proper Chinese character handling
            subject_bytes = subject.encode('utf-8')
            
            if self.imap_backend.utf8_enabled:
                # When UTF-8 is enabled, don't specify charset
                search_criteria = b'SUBJECT "' + subject_bytes + b'"'
                status, email_ids = self.imap_backend.connection.search(None, search_criteria)
            else:
                # Try UTF-8 charset first
                try:
                    search_criteria = b'SUBJECT "' + subject_bytes + b'"'
                    status, email_ids = self.imap_backend.connection.search('UTF-8', search_criteria)
                except Exception as search_error:
                    logging.warning(f"UTF-8 charset search failed: {search_error}")
                    status = 'NO'
                
                # Improved fallback strategy for Chinese subject search
                if status != 'OK':
                    # Try different search approaches for Chinese subjects
                    search_attempts = [
                        # Try searching with quoted subject
                        f'SUBJECT "{subject}"',
                        # Try without quotes  
                        f'SUBJECT {subject}',
                        # Try partial subject search (first 10 chars)
                        f'SUBJECT "{subject[:10]}"' if len(subject) > 10 else None,
                        # Try partial subject search (last 10 chars)  
                        f'SUBJECT "{subject[-10:]}"' if len(subject) > 10 else None
                    ]
                    
                    for attempt in search_attempts:
                        if attempt is None:
                            continue
                        try:
                            status, email_ids = self.imap_backend.connection.search(None, attempt)
                            if status == 'OK' and email_ids[0]:
                                break
                        except:
                            continue
                    
                    # Final ASCII fallback only if all above failed
                    if status != 'OK':
                        ascii_subject = subject.encode('ascii', errors='ignore').decode('ascii')
                        if ascii_subject.strip():
                            status, email_ids = self.imap_backend.connection.search(None, f'SUBJECT "{ascii_subject}"')
                        else:
                            # Return empty if we can't search at all
                            return []
            
            if status != 'OK':
                raise EmailMCPError(f"Search failed: {status}")
            
            id_list = email_ids[0].split()
            return [uid.decode() for uid in reversed(id_list)]
            
        except Exception as e:
            raise EmailMCPError(f"Failed to search by subject: {str(e)}")
    
    def search_by_date_range(self, since_date: str, before_date: Optional[str] = None, 
                           folder: Optional[str] = None) -> List[str]:
        """Search emails by date range (YYYY-MM-DD format)"""
        try:
            # If no folder specified, use INBOX as default
            if not folder:
                folder = 'INBOX'
            
            # Always select folder before searching
            self.imap_backend.select_folder(folder)
            
            self.imap_backend.ensure_connected()
            
            # Construct date search criteria
            search_criteria = f'SINCE "{since_date}"'
            if before_date:
                search_criteria += f' BEFORE "{before_date}"'
            
            status, email_ids = self.imap_backend.connection.search(None, search_criteria)
            
            if status != 'OK':
                raise EmailMCPError(f"Search failed: {status}")
            
            id_list = email_ids[0].split()
            return [uid.decode() for uid in reversed(id_list)]
            
        except Exception as e:
            raise EmailMCPError(f"Failed to search by date: {str(e)}")