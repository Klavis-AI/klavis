from typing import List
import logging
from ..models.email import EmailFolder, MailboxStats
from ..backends.imap_backend import IMAPBackend
from ..utils.exceptions import EmailMCPError, FolderError
from ..utils.validators import validate_folder_name
from ..utils.encode_decode import encode_to_imap_utf7

class FolderService:
    """Folder management service layer"""
    
    def __init__(self, imap_backend: IMAPBackend):
        self.imap_backend = imap_backend
    
    def _quote_folder_name(self, folder_name: str) -> str:
        """Quote folder name if it contains spaces (excluding leading spaces)"""
        # Strip leading/trailing spaces first
        folder_name = folder_name.strip()
        
        # Check if there are spaces in the middle of the folder name
        if ' ' in folder_name:
            # Escape any existing quotes in the folder name
            folder_name = folder_name.replace('"', '\\"')
            # Wrap with quotes
            return f'"{folder_name}"'
        
        return folder_name
    
    def get_folders(self) -> List[EmailFolder]:
        """Get list of all email folders"""
        try:
            return self.imap_backend.list_folders()
        except Exception as e:
            raise EmailMCPError(f"Failed to get folders: {str(e)}")
    
    def create_folder(self, folder_name: str) -> bool:
        """Create new email folder with UTF-8 encoding support"""
        # Validate folder name
        valid, error = validate_folder_name(folder_name)
        if not valid:
            raise FolderError(error)
        
        try:
            self.imap_backend.ensure_connected()
            
            # Quote folder name if it contains spaces

            quoted_folder_name = self._quote_folder_name(folder_name)

            utf7_quoted_folder_name = encode_to_imap_utf7(quoted_folder_name)

            last_error = None

            try:
                logging.info(f"Trying to create folder: {folder_name}")
                
                # Handle UTF-8 encoding for Chinese/Unicode folder names
                if self.imap_backend.utf8_enabled:
                    # Server supports UTF-8, send as UTF-8
                    status, data = self.imap_backend.connection.create(quoted_folder_name)
                else:
                    # For servers without UTF-8 support, try different encodings
                    try:
                        # Try UTF-7 encoding (IMAP standard for non-ASCII)
                        status, data = self.imap_backend.connection.create(utf7_quoted_folder_name)
                    except UnicodeError:
                        # If UTF-7 fails, try direct UTF-8
                        status, data = self.imap_backend.connection.create(quoted_folder_name.encode('utf-8'))
                
                if status == 'OK':
                    logging.info(f"Successfully created folder: {folder_name}")
                    return True
                elif "already exists" in data.lower():
                    logging.warning(f"Folder '{folder_name}' already exists, skip creating it!")
                    return True
                else:
                    logging.warning(f"Failed to create folder '{folder_name}': {status} {data}")
                    last_error = f"Server returned: {status} {data}"
                    
            except Exception as e:
                logging.warning(f"Exception creating folder '{folder_name}': {e}")
                last_error = str(e)
            
            # If all attempts failed
            raise FolderError(f"Failed to create folder '{folder_name}' with any naming convention. Last error: {last_error}")
            
        except Exception as e:
            if isinstance(e, FolderError):
                raise
            raise FolderError(f"Failed to create folder: {str(e)}")
    
    def delete_folder(self, folder_name: str) -> bool:
        """Delete email folder"""
        # Validate folder name
        valid, error = validate_folder_name(folder_name)
        if not valid:
            raise FolderError(error)
        
        # Prevent deletion of system folders
        system_folders = ['INBOX', 'Sent', 'Drafts', 'Trash', 'Spam']
        if folder_name.strip() in system_folders:
            raise FolderError(f"Cannot delete system folder: {folder_name}")
        
        try:
            self.imap_backend.ensure_connected()
            
            # Quote folder name if it contains spaces
            quoted_folder_name = self._quote_folder_name(folder_name)
            utf7_quoted_folder_name = encode_to_imap_utf7(quoted_folder_name)
            
            if self.imap_backend.utf8_enabled:
                status, data = self.imap_backend.connection.delete(quoted_folder_name)
            else:
                status, data = self.imap_backend.connection.delete(utf7_quoted_folder_name)
            
            if status != 'OK':
                raise FolderError(f"Failed to delete folder '{folder_name}': {status}")
            
            return True
            
        except Exception as e:
            raise FolderError(f"Failed to delete folder: {str(e)}")
    
    def get_folder_stats(self, folder_name: str) -> MailboxStats:
        """Get statistics for specific folder"""
        try:
            # Note: select_folder in imap_backend should handle quoting internally
            quoted_folder_name = self._quote_folder_name(folder_name)   
            utf7_quoted_folder_name = encode_to_imap_utf7(quoted_folder_name)

            if self.imap_backend.utf8_enabled:
                total_messages, unread_messages = self.imap_backend.select_folder(quoted_folder_name)
            else:
                total_messages, unread_messages = self.imap_backend.select_folder(utf7_quoted_folder_name)
            
            return MailboxStats(
                folder_name=folder_name,
                total_messages=total_messages,
                unread_messages=unread_messages
            )
            
        except Exception as e:
            raise EmailMCPError(f"Failed to get folder stats: {str(e)}")
    
    def get_unread_count(self, folder_name: str = None) -> int:
        """Get unread message count for folder or all folders"""
        try:
            if folder_name:
                quoted_folder_name = self._quote_folder_name(folder_name)
                utf7_quoted_folder_name = encode_to_imap_utf7(quoted_folder_name)

                if self.imap_backend.utf8_enabled:
                    _, unread_count = self.imap_backend.select_folder(quoted_folder_name)
                else:
                    _, unread_count = self.imap_backend.select_folder(utf7_quoted_folder_name)
                return unread_count
            else:
                # Get unread count for all folders
                folders = self.get_folders()
                total_unread = 0
                for folder in folders:
                    if folder.can_select:
                        total_unread += folder.unread_messages
                return total_unread
                
        except Exception as e:
            raise EmailMCPError(f"Failed to get unread count: {str(e)}")