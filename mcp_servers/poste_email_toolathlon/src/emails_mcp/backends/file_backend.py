import json
import os
import base64
from pathlib import Path
from typing import List
from datetime import datetime
from ..models.email import EmailMessage
from ..utils.exceptions import ValidationError
from ..utils.validators import validate_file_path
from ..utils.email_parser import parse_raw_email
import logging
from email import encoders


class FileBackend:
    """File backend for email import/export operations"""
    
    def __init__(self, email_export_path: str = None, attachment_download_path: str = None):
        self.email_export_path = Path(email_export_path) if email_export_path else None
        self.attachment_download_path = Path(attachment_download_path) if attachment_download_path else None
    
    def export_emails(self, emails: List[EmailMessage], filename_prefix: str = "emails_export", 
                     format: str = 'json') -> str:
        """Export emails to file using configured export path with date-based filename"""
        from datetime import datetime
        
        # Use configured export path or current directory
        if self.email_export_path:
            export_dir = self.email_export_path
        else:
            export_dir = Path.cwd()
        
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate date-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.{format.lower()}"
            export_file = export_dir / filename
            
            if format.lower() == 'json':
                self._export_to_json(emails, export_file)
            elif format.lower() == 'eml':
                self._export_to_eml(emails, export_file)
            else:
                raise ValidationError(f"Unsupported export format: {format}")
            
            return str(export_file)  # Return the actual file path
            
        except Exception as e:
            raise ValidationError(f"Export failed: {str(e)}")
    
    def import_emails(self, import_path: str) -> List[EmailMessage]:
        """Import emails from file with time-based sorting (newest first)"""
        
        # Validate import path
        valid, error = validate_file_path(import_path, must_exist=True)
        if not valid:
            raise ValidationError(f"Invalid import path: {error}")
        
        try:
            import_file = Path(import_path)
            
            emails = []
            if import_file.suffix.lower() == '.json':
                # logging.warning("Importing emails from JSON file")
                emails = self._import_from_json(import_file)
            elif import_file.suffix.lower() == '.eml':
                # logging.warning("Importing emails from EML file")
                emails = self._import_from_eml(import_file)
            elif import_file.is_dir():
                emails = self._import_from_directory(import_file)
            else:
                raise ValidationError(f"Unsupported import format: {import_file.suffix}")
            
            # Sort emails by email_id (oldest first) for consistent import order
            emails.sort(key=lambda email: int(email.email_id) if email.email_id.isdigit() else 0, reverse=False)

            return emails
                
        except Exception as e:
            raise ValidationError(f"Import failed: {str(e)}")
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse email date string to datetime object for sorting"""
        if not date_str:
            return datetime.min.replace(tzinfo=None)  # Put emails without dates at the end
        
        try:
            from email.utils import parsedate_to_datetime
            parsed_date = parsedate_to_datetime(date_str)
            
            # Convert to naive datetime for consistent comparison
            if parsed_date.tzinfo is not None:
                # Convert to UTC and then remove timezone info
                parsed_date = parsed_date.utctimetuple()
                parsed_date = datetime(*parsed_date[:6])
            
            return parsed_date
        except Exception:
            # Fallback to current time if parsing fails (make it naive)
            return datetime.now().replace(tzinfo=None)
    
    def _export_to_json(self, emails: List[EmailMessage], export_file: Path):
        """Export emails to JSON format"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_emails': len(emails),
            'emails': []
        }
        
        for email_obj in emails:
            email_data = {
                'email_id': email_obj.email_id,
                'subject': email_obj.subject,
                'from_addr': email_obj.from_addr,
                'to_addr': email_obj.to_addr,
                'cc_addr': email_obj.cc_addr,
                'bcc_addr': email_obj.bcc_addr,
                'date': email_obj.date,
                'message_id': email_obj.message_id,
                'body_text': email_obj.body_text,
                'body_html': email_obj.body_html,
                'is_read': email_obj.is_read,
                'is_important': email_obj.is_important,
                'folder': email_obj.folder,
                'attachments': [
                    {
                        'filename': att.filename,
                        'content_type': att.content_type,
                        'size': att.size,
                        'content': base64.b64encode(att.content).decode('utf-8') if att.content else None
                    }
                    for att in email_obj.attachments
                ]
            }
            export_data['emails'].append(email_data)
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_to_eml(self, emails: List[EmailMessage], export_path: Path):
        """Export emails to EML format (directory of .eml files)"""
        export_dir = export_path
        if export_path.suffix:
            export_dir = export_path.parent / export_path.stem
        
        export_dir.mkdir(parents=True, exist_ok=True)
        
        for i, email_obj in enumerate(emails):
            if email_obj.raw_message:
                filename = f"{i+1:04d}_{email_obj.email_id}.eml"
                eml_file = export_dir / filename
                
                with open(eml_file, 'wb') as f:
                    f.write(email_obj.raw_message.as_bytes())
    
    def _import_from_json(self, import_file: Path) -> List[EmailMessage]:
        """Import emails from JSON format"""
        with open(import_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        if 'emails' not in import_data:
            raise ValidationError("Invalid JSON format: missing 'emails' key")
        
        emails = []
        for email_data in import_data['emails']:
            try:
                # Create EmailMessage from JSON data
                from ..models.email import EmailAttachment
                
                attachments = []
                for att_data in email_data.get('attachments', []):
                    # 解码附件内容（如果存在）
                    content = None
                    if att_data.get('content'):
                        try:
                            content = base64.b64decode(att_data['content'])
                        except Exception as decode_error:  # 修正：给异常一个具体的变量名
                            # 如果解码失败，保持content为None
                            logging.debug(f"Failed to decode attachment content: {str(decode_error)}")
                            content = None
                    
                    attachment = EmailAttachment(
                        filename=att_data['filename'],
                        content_type=att_data['content_type'],
                        size=att_data['size'],
                        content=content
                    )
                    attachments.append(attachment)
                


                email_obj = EmailMessage(
                    email_id=email_data['email_id'],
                    subject=email_data['subject'],
                    from_addr=email_data['from_addr'],
                    to_addr=email_data['to_addr'],
                    cc_addr=email_data.get('cc_addr'),
                    bcc_addr=email_data.get('bcc_addr'),
                    date=email_data.get('date'),
                    message_id=email_data.get('message_id'),
                    body_text=email_data.get('body_text'),
                    body_html=email_data.get('body_html'),
                    is_read=email_data.get('is_read', False),
                    is_important=email_data.get('is_important', False),
                    folder=email_data.get('folder'),
                    attachments=attachments
                )
                
                # Only create raw_message if there are attachments (for attachment display support)
                if email_data.get('attachments'):
                    # Create a minimal email.message.Message object for JSON imports to support attachment display
                    import email.message
                    from email.mime.multipart import MIMEMultipart
                    from email.mime.base import MIMEBase
                    from email.mime.text import MIMEText
                    
                    msg = MIMEMultipart()
                    msg['Subject'] = email_data['subject']
                    msg['From'] = email_data['from_addr']
                    msg['To'] = email_data['to_addr']
                    if email_data.get('cc_addr'):
                        msg['Cc'] = email_data['cc_addr']
                    if email_data.get('message_id'):
                        msg['Message-ID'] = email_data['message_id']
                    if email_data.get('date'):
                        msg['Date'] = email_data['date']
                    
                    # Add text body if exists
                    if email_data.get('body_text'):
                        text_part = MIMEText(email_data['body_text'], 'plain', 'utf-8')
                        msg.attach(text_part)
                    
                    # Add HTML body if exists
                    if email_data.get('body_html'):
                        html_part = MIMEText(email_data['body_html'], 'html', 'utf-8')
                        msg.attach(html_part)
                    
                    # Add attachments to the message object
                    for att_data in email_data.get('attachments', []):
                        if att_data.get('content'):
                            content_type_parts = att_data['content_type'].split('/')
                            if len(content_type_parts) == 2:
                                maintype, subtype = content_type_parts
                            else:
                                maintype, subtype = 'application', 'octet-stream'
                            
                            part = MIMEBase(maintype, subtype)
                            
                            # 方法A：直接使用（推荐）
                            # 验证 base64 格式但不解码
                            try:
                                # 只验证，不实际解码
                                base64.b64decode(att_data['content'])
                                # 如果验证通过，直接使用
                                part.set_payload(att_data['content'])
                                part['Content-Transfer-Encoding'] = 'base64'
                            except Exception as e:
                                logging.warning(f"Invalid base64 content: {e}")
                                # 设置空附件
                                part.set_payload('')
                                part['Content-Transfer-Encoding'] = 'base64'
                            
                            # 处理文件名...
                            filename = att_data["filename"]
                            try:
                                filename.encode('ascii')
                                part.add_header('Content-Disposition', 'attachment',
                                            filename=filename)
                            except UnicodeEncodeError:
                                part.add_header('Content-Disposition', 'attachment',
                                            filename=('utf-8', '', filename))
                            
                            msg.attach(part)
                    
                    email_obj.raw_message = msg
                else:
                    # No attachments, no need for raw_message
                    email_obj.raw_message = None
                
                emails.append(email_obj)
                
            except KeyError as e:
                raise ValidationError(f"Missing required field in JSON: {str(e)}")
        
        # Sort emails by email_id in descending order
        emails.sort(key=lambda email_obj: int(email_obj.email_id) if email_obj.email_id.isdigit() else 0, reverse=True)
        
        # import pickle
        # os.makedirs("./json", exist_ok=True)
        # with open("./json/all.pkl", "wb") as f:
        #     pickle.dump(emails, f)

        return emails
    
    def _import_from_eml(self, import_file: Path) -> List[EmailMessage]:
        """Import single email from EML format"""
        with open(import_file, 'rb') as f:
            raw_email = f.read()
        
        email_id = import_file.stem
        email_obj = parse_raw_email(raw_email, email_id)
        # import pickle
        # os.makedirs("./eml", exist_ok=True)
        # with open("./eml/all.pkl", "wb") as f:
        #     pickle.dump([email_obj], f)
        return [email_obj]
    
    def _import_from_directory(self, import_dir: Path) -> List[EmailMessage]:
        """Import multiple emails from directory of EML files"""
        emails = []
        
        for eml_file in import_dir.glob('*.eml'):
            try:
                imported_emails = self._import_from_eml(eml_file)
                emails.extend(imported_emails)
            except Exception as e:
                # Log warning but continue with other files
                import logging
                logging.warning(f"Failed to import {eml_file}: {str(e)}")
        
        return emails
    
    def save_attachment(self, attachment_data: bytes, filename: str) -> str:
        """Save attachment data to file using configured download path"""
        
        # Use configured download path or current directory
        if self.attachment_download_path:
            download_dir = self.attachment_download_path
        else:
            download_dir = Path.cwd()
        
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = download_dir / filename
            
            # Avoid overwriting existing files using (1), (2), etc. format
            if file_path.exists():
                name, ext = os.path.splitext(filename)
                counter = 1
                while True:
                    new_filename = f"{name}({counter}){ext}"
                    file_path = download_dir / new_filename
                    if not file_path.exists():
                        break
                    counter += 1
            
            with open(file_path, 'wb') as f:
                f.write(attachment_data)
            
            return str(file_path)
            
        except Exception as e:
            raise ValidationError(f"Failed to save attachment: {str(e)}")