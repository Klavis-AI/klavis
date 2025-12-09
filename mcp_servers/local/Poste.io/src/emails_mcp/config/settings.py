import json
import os
from pathlib import Path
from typing import Optional, List
from ..models.config import EmailConfig, WorkspaceConfig


class ConfigManager:
    """Configuration manager for email MCP server"""
    
    def __init__(self):
        self.workspace_config: Optional[WorkspaceConfig] = None
        self.email_config: Optional[EmailConfig] = None
    
    def load_workspace_config(self, attachment_upload_path: str = None, 
                            attachment_download_path: str = None,
                            email_export_path: str = None, 
                            config_file: str = None) -> WorkspaceConfig:
        """Load workspace configuration"""
        self.workspace_config = WorkspaceConfig(
            attachment_upload_path=attachment_upload_path,
            attachment_download_path=attachment_download_path,
            email_export_path=email_export_path,
            config_file=config_file
        )
        return self.workspace_config
    
    def load_email_config(self, config_file: str) -> EmailConfig:
        """Load email configuration from JSON file (uses first account)"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # if not isinstance(config_data, list):
            #     raise ValueError("Configuration file should contain a list of email accounts")
            
            if not config_data:
                raise ValueError("Configuration file is empty")
            
            # Use first account only
            if isinstance(config_data, list):
                if not config_data:
                    raise ValueError("Configuration file is empty")
                account_data = config_data[0]  # Use first account
            else:
                account_data = config_data  # Single account format
                
            if not isinstance(account_data, dict):
                raise ValueError("Invalid account data format")
            
            email_config = EmailConfig(
                email=account_data.get('email', ''),
                password=account_data.get('password', ''),
                name=account_data.get('name', ''),
                imap_server=account_data.get('imap_server', 'localhost'),
                imap_port=account_data.get('imap_port', 993),
                smtp_server=account_data.get('smtp_server', 'localhost'),
                smtp_port=account_data.get('smtp_port', 587),
                use_ssl=account_data.get('use_ssl', True),
                use_starttls=account_data.get('use_starttls', True)
            )
            
            # Validate required fields
            if not email_config.email or not email_config.password:
                raise ValueError("Email and password are required")
            
            self.email_config = email_config
            return email_config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to load email configuration: {str(e)}")
    
    def get_email_config(self) -> Optional[EmailConfig]:
        """Get email configuration"""
        return self.email_config
    
    def validate_attachment_upload_path(self, file_path: str) -> tuple[bool, str]:
        """Validate if file path is within attachment upload path"""
        if not self.workspace_config or not self.workspace_config.attachment_upload_path:
            return True, ""
        
        try:
            upload_path = Path(self.workspace_config.attachment_upload_path).resolve()
            resolved_path = Path(file_path).resolve()
            
            if not resolved_path.is_relative_to(upload_path):
                return False, f"Error: Path '{file_path}' is outside attachment upload path '{upload_path}'"
            return True, ""
            
        except Exception as e:
            return False, f"Error validating attachment upload path: {str(e)}"
    
    def validate_attachment_download_path(self, file_path: str) -> tuple[bool, str]:
        """Validate if file path is within attachment download path"""
        if not self.workspace_config or not self.workspace_config.attachment_download_path:
            return True, ""
        
        try:
            download_path = Path(self.workspace_config.attachment_download_path).resolve()
            resolved_path = Path(file_path).resolve()
            
            if not resolved_path.is_relative_to(download_path):
                return False, f"Error: Path '{file_path}' is outside attachment download path '{download_path}'"
            return True, ""
            
        except Exception as e:
            return False, f"Error validating attachment download path: {str(e)}"
    
    def validate_email_export_path(self, file_path: str) -> tuple[bool, str]:
        """Validate if file path is within email export path"""
        if not self.workspace_config or not self.workspace_config.email_export_path:
            return True, ""
        
        try:
            export_path = Path(self.workspace_config.email_export_path).resolve()
            resolved_path = Path(file_path).resolve()
            
            if not resolved_path.is_relative_to(export_path):
                return False, f"Error: Path '{file_path}' is outside email export path '{export_path}'"
            return True, ""
            
        except Exception as e:
            return False, f"Error validating email export path: {str(e)}"
    
    def get_unique_download_path(self, filename: str) -> str:
        """Get unique path for downloading file, adding (1), (2), etc. if file exists"""
        if not self.workspace_config or not self.workspace_config.attachment_download_path:
            return filename
        
        base_path = Path(self.workspace_config.attachment_download_path)
        file_path = base_path / filename
        
        if not file_path.exists():
            return str(file_path)
        
        # Extract name and extension
        stem = file_path.stem
        suffix = file_path.suffix
        
        counter = 1
        while True:
            new_filename = f"{stem}({counter}){suffix}"
            new_path = base_path / new_filename
            if not new_path.exists():
                return str(new_path)
            counter += 1


# Global config manager instance
config_manager = ConfigManager()