import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import List, Optional
from ..models.config import EmailConfig
from ..utils.exceptions import ConnectionError, AuthenticationError, SendEmailError
from ..utils.validators import validate_email_list, validate_file_path
from ..config.settings import ConfigManager


class SMTPBackend:
    """SMTP backend for sending emails"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.connection: Optional[smtplib.SMTP] = None
    
    def connect(self) -> bool:
        """Establish SMTP connection"""
        try:
            self.connection = smtplib.SMTP(
                self.config.smtp_server,
                self.config.smtp_port
            )
            
            # Enable debugging for development
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                self.connection.set_debuglevel(1)
            
            # Start TLS if configured
            if self.config.use_starttls:
                self.connection.starttls()
            
            # Login only if password is provided and server supports auth
            if self.config.password and self.config.password.strip():
                try:
                    # Check if server supports authentication
                    if 'auth' in self.connection.esmtp_features:
                        self.connection.login(self.config.email, self.config.password)
                        logging.info(f"SMTP authenticated for {self.config.email}")
                    else:
                        logging.info(f"SMTP server doesn't support auth, proceeding without authentication")
                except smtplib.SMTPAuthenticationError as e:
                    # If auth fails but server might allow sending without auth, try to continue
                    logging.warning(f"SMTP authentication failed: {str(e)}, trying without auth")
            else:
                logging.info(f"No password provided, proceeding without authentication")
            
            logging.info(f"SMTP connected for {self.config.email}")
            return True
            
        except Exception as e:
            logging.error(f"SMTP connection failed: {str(e)}")
            raise ConnectionError(f"SMTP connection failed: {str(e)}")
    
    def disconnect(self):
        """Close SMTP connection"""
        if self.connection:
            try:
                self.connection.quit()
            except:
                pass
            finally:
                self.connection = None
    
    def ensure_connected(self):
        """Ensure SMTP connection is active"""
        if not self.connection:
            logging.debug("No SMTP connection, connecting...")
            self.connect()
        
        # Test connection with more robust checking
        try:
            status = self.connection.noop()
            if status[0] != 250:  # NOOP should return 250 OK
                raise Exception(f"NOOP returned {status}")
        except Exception as e:
            logging.warning(f"SMTP connection test failed: {e}, reconnecting...")
            self.disconnect()
            self.connect()
    
    def send_email(self, to: str, subject: str, body: str, 
                   html_body: Optional[str] = None,
                   cc: Optional[str] = None, 
                   bcc: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> tuple[bool, Optional[str]]:
        """Send email with optional HTML, CC, BCC, and attachments
        
        Returns:
            tuple[bool, Optional[str]]: (success, message_string_for_saving)
        """
        
        # Validate recipients
        valid, error = validate_email_list(to)
        if not valid:
            raise SendEmailError(f"Invalid TO addresses: {error}")
        
        if cc:
            valid, error = validate_email_list(cc)
            if not valid:
                raise SendEmailError(f"Invalid CC addresses: {error}")
        
        if bcc:
            valid, error = validate_email_list(bcc)
            if not valid:
                raise SendEmailError(f"Invalid BCC addresses: {error}")
        
        self.ensure_connected()
        
        try:
            # Create message
            if html_body or attachments:
                msg = MIMEMultipart('alternative' if html_body else 'mixed')
            else:
                msg = MIMEText(body, 'plain', 'utf-8')
                
            if isinstance(msg, MIMEMultipart):
                # Add text part
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
                
                # Add HTML part if provided
                if html_body:
                    html_part = MIMEText(html_body, 'html', 'utf-8')
                    msg.attach(html_part)
            
            # Set headers with proper Chinese encoding
            from email.header import Header
            
            # Encode subject for Chinese characters
            msg['Subject'] = Header(subject, 'utf-8')
            
            # Format From header with name if provided, with Chinese support
            if self.config.name:
                # Encode name for Chinese characters
                encoded_name = Header(self.config.name, 'utf-8')
                msg['From'] = formataddr((str(encoded_name), self.config.email))
            else:
                msg['From'] = self.config.email
            msg['To'] = to
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Add attachments
            if attachments:
                # Ensure we have a multipart message
                if not isinstance(msg, MIMEMultipart):
                    original_msg = msg
                    msg = MIMEMultipart('mixed')
                    msg['Subject'] = subject
                    # Format From header with name if provided
                    if self.config.name:
                        msg['From'] = formataddr((self.config.name, self.config.email))
                    else:
                        msg['From'] = self.config.email
                    msg['To'] = to
                    if cc:
                        msg['Cc'] = cc
                    if bcc:
                        msg['Bcc'] = bcc
                    msg.attach(original_msg)
                
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # Prepare recipient list
            recipients = [addr.strip() for addr in to.split(',')]
            if cc:
                recipients.extend([addr.strip() for addr in cc.split(',')])
            if bcc:
                recipients.extend([addr.strip() for addr in bcc.split(',')])
            
            # Send email
            self.connection.send_message(msg, to_addrs=recipients)
            logging.info(f"Email sent successfully to {to}")
            
            # Return success and the complete message for saving to Sent folder
            return True, msg.as_string()
            
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            raise SendEmailError(f"Failed to send email: {str(e)}")
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach file to message"""
        # Validate file path
        valid, error = validate_file_path(file_path, must_exist=True)
        if not valid:
            raise SendEmailError(f"Attachment error: {error}")
        
        # Validate attachment upload path if configured
        config_manager = ConfigManager()
        path_valid, path_error = config_manager.validate_attachment_upload_path(file_path)
        if not path_valid:
            raise SendEmailError(f"Attachment path validation failed: {path_error}")
        
        try:
            with open(file_path, 'rb') as f:
                attachment_data = f.read()
            
            # Create attachment
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(attachment_data)
            encoders.encode_base64(attachment)
            
            # Add header
            filename = os.path.basename(file_path)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(attachment)
            logging.debug(f"Attached file: {filename}")
            
        except Exception as e:
            raise SendEmailError(f"Failed to attach file {file_path}: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test SMTP connection without sending email"""
        try:
            self.ensure_connected()
            return True
        except Exception:
            return False