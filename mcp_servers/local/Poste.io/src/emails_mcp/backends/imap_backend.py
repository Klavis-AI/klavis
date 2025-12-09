import imaplib
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from ..models.config import EmailConfig
from ..models.email import EmailFolder, EmailMessage
from ..utils.exceptions import ConnectionError, AuthenticationError, FolderError
from ..utils.email_parser import parse_raw_email
from ..utils.encode_decode import encode_to_imap_utf7, decode_from_imap_utf7

class IMAPBackend:
    """IMAP backend for email operations"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.current_folder: Optional[str] = None
        self.last_accessed = datetime.now()
        self.utf8_enabled = False
    
    def connect(self) -> bool:
        """Establish IMAP connection"""
        try:
            if self.config.use_ssl:
                self.connection = imaplib.IMAP4_SSL(
                    self.config.imap_server,
                    self.config.imap_port
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.config.imap_server,
                    self.config.imap_port
                )
            
            # Login
            self.connection.login(self.config.email, self.config.password)
            self.last_accessed = datetime.now()
            
            # Try to enable UTF-8 support if available
            self._enable_utf8_support()
            
            logging.info(f"IMAP connected for {self.config.email}")
            return True
            
        except imaplib.IMAP4.error as e:
            logging.error(f"IMAP authentication failed: {str(e)}")
            raise AuthenticationError(f"IMAP login failed: {str(e)}")
        except Exception as e:
            logging.error(f"IMAP connection failed: {str(e)}")
            raise ConnectionError(f"IMAP connection failed: {str(e)}")
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            finally:
                self.connection = None
                self.current_folder = None
                self.utf8_enabled = False
    
    def ensure_connected(self):
        """Ensure IMAP connection is active"""
        if not self.connection:
            self.connect()
        
        # Test connection with NOOP
        try:
            self.connection.noop()
            self.last_accessed = datetime.now()
        except:
            logging.warning("IMAP connection lost, reconnecting...")
            self.disconnect()
            self.connect()
    
    def _enable_utf8_support(self):
        """Try to enable UTF-8 support on IMAP server"""
        try:
            # Check if server supports UTF8 capability
            capabilities = self.connection.capability()
            if capabilities[0] == 'OK':
                capability_list = capabilities[1][0].decode().upper().split()
                if 'UTF8=ACCEPT' in capability_list or 'UTF8=ONLY' in capability_list:
                    # Try to enable UTF-8 support
                    result = self.connection.enable('UTF8=ACCEPT')
                    if result[0] == 'OK':
                        self.utf8_enabled = True
                        logging.info("UTF-8 support enabled for IMAP connection")
                    else:
                        logging.warning("Failed to enable UTF-8 support")
                else:
                    logging.info("Server does not support UTF8=ACCEPT capability")
        except Exception as e:
            logging.warning(f"Could not check/enable UTF-8 support: {str(e)}")
            self.utf8_enabled = False
    
    def _quote_folder_name(self, folder_name: str) -> str:
        """Quote folder name if it contains spaces (excluding leading/trailing spaces)"""
        # Strip leading/trailing spaces first
        folder_name = folder_name.strip()
        
        # Check if there are spaces in the middle of the folder name
        if ' ' in folder_name:
            # Escape any existing quotes in the folder name
            folder_name = folder_name.replace('"', '\\"')
            # Wrap with quotes
            return f'"{folder_name}"'
        
        return folder_name

    def select_folder(self, folder: str) -> Tuple[int, int]:
        """Select email folder and return (total_messages, unread_messages)"""
        self.ensure_connected()
        logging.info(f"尝试选中文件夹: {folder}")
        try:
            # Quote folder name if necessary
            quoted_folder_name = self._quote_folder_name(folder)
            utf7_quoted_folder_name = encode_to_imap_utf7(quoted_folder_name)

            if self.utf8_enabled:
                status, data = self.connection.select(quoted_folder_name)  
            else:
                status, data = self.connection.select(utf7_quoted_folder_name)
            
            if status != 'OK':
                raise FolderError(f"Failed to select folder '{folder}': {status}")
            
            self.current_folder = folder  # Store the original folder name without quotes
            total_messages = int(
                data[0]) if data[0] else 0
            
            # Get unread count
            status, unread_data = self.connection.search(None, 'UNSEEN')
            unread_messages = len(unread_data[0].split()) if status == 'OK' and unread_data[0] else 0
            
            return total_messages, unread_messages
            
        except Exception as e:
            raise FolderError(f"Error selecting folder '{folder}': {str(e)}")
    
    def list_folders(self) -> List[EmailFolder]:
        """List all available folders"""
        self.ensure_connected()
        
        try:
            status, folders = self.connection.list()
            if status != 'OK':
                raise FolderError(f"Failed to list folders: {status}")
            
            folder_list = []
            for folder in folders:
                if self.utf8_enabled:
                    folder_info = folder.decode('utf-8')
                else:
                    folder_info = decode_from_imap_utf7(folder.decode('utf-8'))
                logging.debug(f"Parsing folder info: {folder_info}")
                
                # Parse folder name from IMAP response
                # Format can be: '(\\HasNoChildren) "." "INBOX"' or '(\\HasNoChildren) "." INBOX'
                parts = folder_info.split('"')
                
                folder_name = None
                if len(parts) >= 3:
                    # If folder name is quoted: '(flags) "sep" "name"'
                    # The folder name is typically the last quoted part (parts[3] if exists, otherwise parts[2])
                    if len(parts) >= 4 and parts[3].strip():
                        folder_name = parts[3].strip()
                    elif len(parts) >= 3 and parts[2].strip() and parts[2].strip() not in ['.', '/', '\\']:
                        folder_name = parts[2].strip()
                else:
                    # If folder name is not quoted: '(flags) "sep" name'
                    # Split by spaces and take the last part
                    space_parts = folder_info.split()
                    if len(space_parts) >= 3:
                        folder_name = space_parts[-1]
                
                # Skip invalid folder names (root folders, empty names, etc.)
                if not folder_name or folder_name in [".", ".."]:
                    continue
                
                # Check if folder is selectable
                is_noselect = '\\Noselect' in folder_info
                
                # Try to get folder stats for selectable folders
                if not is_noselect:
                    try:
                        total, unread = self.select_folder(folder_name)
                        folder_obj = EmailFolder(
                            name=folder_name,
                            total_messages=total,
                            unread_messages=unread,
                            can_select=True
                        )
                    except:
                        # If we can't select the folder, mark it as non-selectable
                        folder_obj = EmailFolder(
                            name=folder_name,
                            can_select=False
                        )
                else:
                    # Folder marked as non-selectable by server
                    folder_obj = EmailFolder(
                        name=folder_name,
                        can_select=False
                    )
                
                folder_list.append(folder_obj)
            
            return folder_list
            
        except Exception as e:
            raise FolderError(f"Error listing folders: {str(e)}")
    
    def get_email_ids(self, folder: str, limit: Optional[int] = None) -> List[str]:
        """Get email IDs from folder (newest first)"""
        quoted_folder_name = self._quote_folder_name(folder)
        utf7_quoted_folder_name = encode_to_imap_utf7(quoted_folder_name)

        if self.utf8_enabled:
            total, _ = self.select_folder(quoted_folder_name)
        else:
            total, _ = self.select_folder(utf7_quoted_folder_name)
        
        if total == 0:
            return []
        
        try:
            # Get all email IDs
            status, email_ids = self.connection.search(None, 'ALL')
            if status != 'OK':
                raise FolderError(f"Failed to search emails: {status}")
            
            id_list = email_ids[0].split()
            # Reverse to get newest first
            id_list = [uid.decode() for uid in reversed(id_list)]
            
            if limit:
                id_list = id_list[:limit]
            
            return id_list
            
        except Exception as e:
            raise FolderError(f"Error getting email IDs: {str(e)}")
    
    def fetch_email(self, email_id: str) -> EmailMessage:
        """Fetch single email by ID"""
        self.ensure_connected()
        
        try:
            # Fetch email content and flags separately for better reliability
            # First get the RFC822 content
            status, content_data = self.connection.fetch(email_id, '(RFC822)')
            if status != 'OK':
                raise FolderError(f"Failed to fetch email content {email_id}: {status}")
            
            # Then get current flags separately
            status, flag_data = self.connection.fetch(email_id, '(FLAGS)')
            if status != 'OK':
                raise FolderError(f"Failed to fetch email flags {email_id}: {status}")
            
            # Extract email content
            raw_email = None
            if content_data and len(content_data) > 0:
                for item in content_data:
                    if isinstance(item, tuple) and len(item) == 2:
                        # item[1] should be the email content
                        if isinstance(item[1], bytes) and len(item[1]) > 0:
                            raw_email = item[1]
                            break
            
            if not raw_email:
                raise FolderError(f"No email content found for email {email_id}")
            
            # Extract flags
            flags = []
            for item in flag_data:
                if isinstance(item, bytes):
                    # Direct bytes response like b'6 (FLAGS (\\Seen \\Flagged))'
                    header = item.decode()
                    if 'FLAGS' in header:
                        import re
                        flag_match = re.search(r'FLAGS \(([^)]*)\)', header)
                        if flag_match:
                            flags_str = flag_match.group(1)
                            flags = flags_str.split() if flags_str.strip() else []
                            logging.debug(f"Extracted current flags for email {email_id}: {flags}")
                            break
                elif isinstance(item, tuple) and len(item) == 2:
                    # Tuple response
                    header = item[0].decode() if isinstance(item[0], bytes) else str(item[0])
                    if 'FLAGS' in header:
                        import re
                        flag_match = re.search(r'FLAGS \(([^)]*)\)', header)
                        if flag_match:
                            flags_str = flag_match.group(1)
                            flags = flags_str.split() if flags_str.strip() else []
                            logging.debug(f"Extracted current flags for email {email_id}: {flags}")
                            break
            
            email_obj = parse_raw_email(raw_email, email_id)
            email_obj.folder = self.current_folder
            
            # Set status based on current IMAP flags
            email_obj.is_read = '\\Seen' in flags
            email_obj.is_important = '\\Flagged' in flags
            
            logging.debug(f"Email {email_id} status: read={email_obj.is_read}, important={email_obj.is_important}")
            
            return email_obj
            
        except Exception as e:
            logging.error(f"Error fetching email {email_id}: {str(e)}")
            raise
    
    def search_emails(self, query: str, folder: str = None) -> List[str]:
        """Search emails and return email IDs"""
        self.ensure_connected()
        
        # If no folder specified, use INBOX as default
        if not folder:
            folder = 'INBOX'
        
        # Always select folder before searching
        self.select_folder(folder)
        
        try:
            # Handle Unicode/Chinese characters in search query
            # Based on StackOverflow solution: need to encode Unicode strings to UTF-8 bytes
            query_bytes = query.encode('utf-8')
            
            # Try UTF-8 search first if server supports it
            # Use TEXT search which covers all text content (subject, body, headers)
            # This is more reliable than OR combinations for UTF-8 content
            if self.utf8_enabled:
                # When UTF-8 is enabled, we should NOT specify charset parameter
                # Use TEXT to search all text content
                search_criteria = b'TEXT "' + query_bytes + b'"'
                status, email_ids = self.connection.search(None, search_criteria)
            else:
                # For servers without UTF-8 support, try UTF-8 charset parameter
                try:
                    # Use TEXT with UTF-8 charset
                    search_criteria = b'TEXT "' + query_bytes + b'"'
                    status, email_ids = self.connection.search('UTF-8', search_criteria)
                except Exception as search_error:
                    logging.warning(f"UTF-8 charset search failed: {search_error}")
                    status = 'NO'
            
            if status != 'OK':
                # Fallback to ASCII search if UTF-8 search fails
                logging.warning(f"UTF-8 search failed, trying ASCII fallback for query: {query}")
                ascii_query = query.encode('ascii', errors='ignore').decode('ascii')
                if ascii_query.strip():  # Only search if we have non-empty ASCII query
                    search_criteria_ascii = f'(OR SUBJECT "{ascii_query}" FROM "{ascii_query}" BODY "{ascii_query}")'
                    status, email_ids = self.connection.search(None, search_criteria_ascii)
                else:
                    # If ASCII conversion results in empty string, return empty results
                    logging.warning(f"Query '{query}' contains only non-ASCII characters, no ASCII fallback possible")
                    return []
                
                if status != 'OK':
                    raise FolderError(f"Search failed: {status}")
            
            id_list = email_ids[0].split()
            # Return newest first
            return [uid.decode() for uid in reversed(id_list)]
            
        except Exception as e:
            logging.error(f"Error searching emails with query '{query}': {str(e)}")
            raise FolderError(f"Error searching emails: {str(e)}")
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read
        
        Returns:
            bool: True if operation was successful
        """
        self.ensure_connected()
        
        try:
            result = self.connection.store(email_id, '+FLAGS', '\\Seen')
            if result[0] != 'OK':
                logging.error(f"Failed to mark email {email_id} as read: {result[1]}")
                return False
            
            # Force synchronization to ensure the change is applied
            self.connection.noop()  # Send NOOP to sync with server
            logging.debug(f"Successfully marked email {email_id} as read")
            return True
            
        except Exception as e:
            logging.error(f"Error marking email {email_id} as read: {str(e)}")
            return False
    
    def mark_as_unread(self, email_id: str) -> bool:
        """Mark email as unread
        
        Returns:
            bool: True if operation was successful
        """
        self.ensure_connected()
        
        try:
            result = self.connection.store(email_id, '-FLAGS', '\\Seen')
            if result[0] != 'OK':
                logging.error(f"Failed to mark email {email_id} as unread: {result[1]}")
                return False
            
            # Force synchronization to ensure the change is applied
            self.connection.noop()  # Send NOOP to sync with server
            logging.debug(f"Successfully marked email {email_id} as unread")
            return True
            
        except Exception as e:
            logging.error(f"Error marking email {email_id} as unread: {str(e)}")
            return False
    
    def mark_as_important(self, email_id: str) -> bool:
        """Mark email as important (flagged)
        
        Returns:
            bool: True if operation was successful
        """
        self.ensure_connected()
        
        try:
            result = self.connection.store(email_id, '+FLAGS', '\\Flagged')
            if result[0] != 'OK':
                logging.error(f"Failed to mark email {email_id} as important: {result[1]}")
                return False
            
            # Force synchronization to ensure the change is applied
            self.connection.noop()  # Send NOOP to sync with server
            logging.debug(f"Successfully marked email {email_id} as important")
            return True
            
        except Exception as e:
            logging.error(f"Error marking email {email_id} as important: {str(e)}")
            return False
    
    def mark_as_not_important(self, email_id: str) -> bool:
        """Remove important flag from email
        
        Returns:
            bool: True if operation was successful
        """
        self.ensure_connected()
        
        try:
            result = self.connection.store(email_id, '-FLAGS', '\\Flagged')
            if result[0] != 'OK':
                logging.error(f"Failed to remove important flag from email {email_id}: {result[1]}")
                return False
            
            # Force synchronization to ensure the change is applied
            self.connection.noop()  # Send NOOP to sync with server
            logging.debug(f"Successfully removed important flag from email {email_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error removing important flag from email {email_id}: {str(e)}")
            return False
    
    def delete_email(self, email_id: str):
        """Mark email for deletion"""
        self.ensure_connected()
        
        try:
            self.connection.store(email_id, '+FLAGS', '\\Deleted')
            self.connection.expunge()
        except Exception as e:
            logging.error(f"Error deleting email {email_id}: {str(e)}")
            raise FolderError(f"Failed to delete email: {str(e)}")
    
    def move_email(self, email_id: str, target_folder: str) -> Optional[str]:
        """Move email to another folder with UTF-8 encoding support
        
        Returns:
            Optional[str]: New email ID in target folder, or None if move failed
        """
        self.ensure_connected()
        
        try:
            # First, verify the email exists in current folder
            status, data = self.connection.fetch(email_id, '(FLAGS)')
            if status != 'OK':
                raise FolderError(f"Email {email_id} not found in current folder")
            
            # Handle UTF-8 encoding for target folder name
            quoted_target_folder = self._quote_folder_name(target_folder)
            utf7_quoted_target_folder = encode_to_imap_utf7(quoted_target_folder)
            
            # Copy to target folder
            if self.utf8_enabled:
                copy_result = self.connection.copy(email_id, quoted_target_folder)
            else:
                copy_result = self.connection.copy(email_id, utf7_quoted_target_folder)
            if copy_result[0] != 'OK':
                raise FolderError(f"Failed to copy email to {target_folder}: {copy_result[1]}")
            
            # Mark as deleted in current folder
            store_result = self.connection.store(email_id, '+FLAGS', '\\Deleted')
            if store_result[0] != 'OK':
                logging.warning(f"Failed to mark email {email_id} as deleted: {store_result[1]}")
            
            # Expunge to actually remove from current folder
            expunge_result = self.connection.expunge()
            if expunge_result[0] != 'OK':
                logging.warning(f"Failed to expunge deleted emails: {expunge_result[1]}")
            
            logging.info(f"Successfully moved email {email_id} to {target_folder}")
            
            # Note: We can't easily get the new UID without searching, 
            # but the move operation itself is successful
            return None  # Could be enhanced to return new UID if needed
            
        except Exception as e:
            logging.error(f"Error moving email {email_id} to {target_folder}: {str(e)}")
            raise FolderError(f"Failed to move email: {str(e)}")
    
    def append_message(self, folder: str, message: str, flags: str = '\\Seen') -> bool:
        """Append a message to the specified folder with UTF-8 support"""
        self.ensure_connected()
        
        try:
            # Encode folder name for IMAP operations
            quoted_folder = self._quote_folder_name(folder)
            utf7_quoted_folder = encode_to_imap_utf7(quoted_folder)
            
            # Use IMAP APPEND command to add message to folder
            if self.utf8_enabled:
                result = self.connection.append(quoted_folder, flags, None, message.encode('utf-8'))
            else:
                result = self.connection.append(utf7_quoted_folder, flags, None, message.encode('utf-8'))
            if result[0] == 'OK':
                logging.info(f"Message appended to {folder}")
                return True
            else:
                logging.error(f"Failed to append message to {folder}: {result}")
                return False
        except Exception as e:
            logging.error(f"Error appending message to {folder}: {str(e)}")
            raise FolderError(f"Failed to append message to {folder}: {str(e)}")