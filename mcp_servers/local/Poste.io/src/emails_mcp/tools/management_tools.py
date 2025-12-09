from typing import List
from mcp.server.fastmcp import FastMCP
from ..services.draft_service import DraftService


def _reconstruct_email_message(email_obj) -> str:
    """Reconstruct email message from EmailMessage object"""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formatdate
    
    # Create message
    if email_obj.body_html:
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(email_obj.body_text or '', 'plain', 'utf-8'))
        msg.attach(MIMEText(email_obj.body_html, 'html', 'utf-8'))
    else:
        msg = MIMEText(email_obj.body_text or '', 'plain', 'utf-8')
    
    # Set headers
    msg['Subject'] = email_obj.subject or ''
    msg['From'] = email_obj.from_addr or ''
    msg['To'] = email_obj.to_addr or ''
    if email_obj.cc_addr:
        msg['Cc'] = email_obj.cc_addr
    if email_obj.bcc_addr:
        msg['Bcc'] = email_obj.bcc_addr
    if email_obj.message_id:
        msg['Message-ID'] = email_obj.message_id
    if email_obj.date:
        msg['Date'] = email_obj.date
    else:
        msg['Date'] = formatdate(localtime=True)
    
    return msg.as_string()

def register_management_tools(mcp: FastMCP, draft_service: DraftService, email_service):
    """Register management and utility MCP tools"""
    
    @mcp.tool()
    async def check_connection() -> str:
        """Check email server connection status"""
        try:
            imap_ok, smtp_ok = email_service.check_connection()
            
            status = "Connection Status:\n"
            status += f"IMAP: {'✓ Connected' if imap_ok else '✗ Failed'}\n"
            status += f"SMTP: {'✓ Connected' if smtp_ok else '✗ Failed'}\n"
            
            if imap_ok and smtp_ok:
                status += "\nAll connections are working properly"
            elif imap_ok:
                status += "\nWarning: SMTP connection failed - cannot send emails"
            elif smtp_ok:
                status += "\nWarning: IMAP connection failed - cannot receive emails"
            else:
                status += "\nError: Both connections failed - check configuration"
            
            return status
            
        except Exception as e:
            return f"Error checking connection: {str(e)}"
    
    @mcp.tool()
    async def get_email_headers(email_id: str) -> str:
        """Get complete email headers for technical analysis
        
        Args:
            email_id: Email ID to get headers for
        """
        try:
            email = email_service.imap_backend.fetch_email(email_id)
            
            if not email.raw_message:
                return f"No raw message data available for email {email_id}"
            
            output = f"Email Headers for ID: {email_id}\n"
            output += "=" * 50 + "\n"
            
            # Get all headers from raw message
            for header, value in email.raw_message.items():
                output += f"{header}: {value}\n"
            
            return output
            
        except Exception as e:
            return f"Error getting email headers: {str(e)}"
    
    @mcp.tool()
    async def save_draft(subject: str, body: str, html_body: str = None,
                        to: str = None, cc: str = None, bcc: str = None) -> str:
        """Save email draft
        
        Args:
            subject: Email subject
            body: Plain text body
            html_body: HTML body content (optional)
            to: Recipient email address(es) (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        """
        try:
            draft_id = draft_service.save_draft(
                subject=subject,
                body=body,
                html_body=html_body,
                to=to,
                cc=cc,
                bcc=bcc
            )
            
            return f"Draft saved successfully with ID: {draft_id}"
            
        except Exception as e:
            return f"Error saving draft: {str(e)}"
    
    @mcp.tool()
    async def get_drafts(page: int = 1, page_size: int = 20) -> str:
        """Get list of saved drafts
        
        Args:
            page: Page number starting from 1 (default: 1)
            page_size: Number of drafts per page (default: 20)
        """
        try:
            result = draft_service.get_drafts(page, page_size)
            
            if result['total_drafts'] == 0:
                return "No drafts found"
            
            output = f"Drafts (Page {result['current_page']}/{result['total_pages']}):\n"
            output += f"Total drafts: {result['total_drafts']}\n\n"
            
            for i, draft in enumerate(result['drafts'], 1):
                output += f"{(result['current_page']-1)*result['page_size'] + i}. "
                output += f"ID: {draft['draft_id']}\n"
                output += f"   Subject: {draft['subject']}\n"
                output += f"   To: {draft.get('to', 'Not set')}\n"
                output += f"   Updated: {draft['updated_at']}\n\n"
            
            return output
            
        except Exception as e:
            return f"Error getting drafts: {str(e)}"
    
    @mcp.tool()
    async def update_draft(draft_id: str, subject: str = None, body: str = None,
                          html_body: str = None, to: str = None, cc: str = None, bcc: str = None) -> str:
        """Update existing draft
        
        Args:
            draft_id: Draft ID to update
            subject: Email subject (optional)
            body: Plain text body (optional)
            html_body: HTML body content (optional)
            to: Recipient email address(es) (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        """
        try:
            success = draft_service.update_draft(
                draft_id=draft_id,
                subject=subject,
                body=body,
                html_body=html_body,
                to=to,
                cc=cc,
                bcc=bcc
            )
            
            if success:
                return f"Draft {draft_id} updated successfully"
            else:
                return f"Failed to update draft {draft_id}"
                
        except Exception as e:
            return f"Error updating draft: {str(e)}"
    
    @mcp.tool()
    async def delete_draft(draft_id: str) -> str:
        """Delete draft
        
        Args:
            draft_id: Draft ID to delete
        """
        try:
            success = draft_service.delete_draft(draft_id)
            
            if success:
                return f"Draft {draft_id} deleted successfully"
            else:
                return f"Failed to delete draft {draft_id}"
                
        except Exception as e:
            return f"Error deleting draft: {str(e)}"
    
    @mcp.tool()
    async def export_emails(folder: str = None, export_path: str = "emails_export.json", max_emails: int = None, export_all_folders: bool = False) -> str:
        """Export emails to file for backup
        
        Args:
            folder: Specific folder to export (mutually exclusive with export_all_folders)
            export_path: Path where to save the export file  
            max_emails: Maximum number of emails to export (optional, exports all if not specified)
            export_all_folders: Export from all folders instead of just one (default: False)
        """
        try:
            from ..backends.file_backend import FileBackend
            from ..config import config_manager
            from ..services.folder_service import FolderService
            
            # Initialize services
            folder_service = FolderService(email_service.imap_backend)
            
            # Determine which folders to export from
            if export_all_folders and folder:
                return "Error: Cannot specify both 'folder' and 'export_all_folders=True'"
            
            folders_to_export = []
            if export_all_folders:
                # Get all selectable folders
                all_folders = folder_service.get_folders()
                folders_to_export = [f.name for f in all_folders if f.can_select]
                print(f"Exporting from all folders: {folders_to_export}")
            else:
                # Export from single folder
                target_folder = folder or "INBOX"
                folders_to_export = [target_folder]
            
            # Export from all specified folders
            all_emails = []
            folder_stats = {}
            
            for folder_name in folders_to_export:
                print(f"Processing folder: {folder_name}")
                folder_emails = []
                page = 1
                page_size = 100  # Process in smaller batches
                
                while True:
                    try:
                        result = email_service.get_emails(folder_name, page=page, page_size=page_size)
                        
                        if not result.emails:
                            break
                            
                        folder_emails.extend(result.emails)
                        
                        # Check if we've reached the global maximum
                        if max_emails and len(all_emails) + len(folder_emails) >= max_emails:
                            remaining = max_emails - len(all_emails)
                            folder_emails = folder_emails[:remaining]
                            break
                        
                        # Check if we've got all emails from this folder
                        if page * page_size >= result.total_results:
                            break
                            
                        page += 1
                        
                    except Exception as e:
                        print(f"Error reading from folder {folder_name}, page {page}: {str(e)}")
                        break
                
                # Add folder emails to total
                all_emails.extend(folder_emails)
                folder_stats[folder_name] = len(folder_emails)
                
                # Check global limit
                if max_emails and len(all_emails) >= max_emails:
                    break
            
            if not all_emails:
                folders_desc = "all folders" if export_all_folders else folders_to_export[0]
                return f"No emails found to export from {folders_desc}"
            
            # Validate export path
            workspace_config = config_manager.workspace_config
            file_backend = FileBackend(
                email_export_path=workspace_config.email_export_path if workspace_config else None,
                attachment_download_path=workspace_config.attachment_download_path if workspace_config else None
            )
            
            export_name = "all_folders_export" if export_all_folders else f"{folders_to_export[0]}_export"
            exported_file = file_backend.export_emails(all_emails, export_name, 'json')
            
            # Build result message
            result_msg = f"Successfully exported {len(all_emails)} emails to {exported_file}\n"
            
            if export_all_folders:
                result_msg += "Export breakdown by folder:\n"
                for folder_name, count in folder_stats.items():
                    result_msg += f"  - {folder_name}: {count} emails\n"
            
            return result_msg.rstrip()
                
        except Exception as e:
            return f"Error exporting emails: {str(e)}"
    
    @mcp.tool()
    async def import_emails(import_path: str, target_folder: str = None, preserve_folders: bool = True) -> str:
        """Import emails from backup file to IMAP server
        
        Args:
            import_path: Path to import file (.json or .eml) or a directory
            target_folder: Target folder for imported emails (if preserve_folders=False)
            preserve_folders: Whether to preserve original folder structure (default: True)
        """
        try:
            from ..backends.file_backend import FileBackend
            from ..config import config_manager
            
            # Validate import path  
            workspace_config = config_manager.workspace_config
            file_backend = FileBackend(
                email_export_path=workspace_config.email_export_path if workspace_config else None,
                attachment_download_path=workspace_config.attachment_download_path if workspace_config else None
            )
            
            imported_emails = file_backend.import_emails(import_path)
            
            if not imported_emails:
                return f"No emails found in import file {import_path}"
            
            # 按email_id从大到小排序，确保导入时保持原始顺序
            # 因为get_emails返回的是newest first，所以ID越大的邮件越新
            # 倒序导入可以保持原来的头部（最老）和尾部（最新）顺序
            try:
                imported_emails.sort(key=lambda x: int(x.email_id) if x.email_id.isdigit() else 0, reverse=False)
                print(f"Sorted {len(imported_emails)} emails by ID for proper import order")
            except Exception as e:
                print(f"Warning: Could not sort emails by ID: {str(e)}, importing in original order")
            
            # Import emails to IMAP server
            success_count = 0
            failed_count = 0
            failed_reasons = []
            folder_stats = {}
            
            for email_obj in imported_emails:
                try:
                    # Determine target folder
                    if preserve_folders and email_obj.folder:
                        import_folder = email_obj.folder
                    else:
                        import_folder = target_folder or "INBOX"
                    
                    # Ensure target folder exists and is accessible
                    folder_created = False
                    try:
                        email_service.imap_backend.select_folder(import_folder)
                    except Exception as e:
                        # If folder doesn't exist, try to create it
                        if preserve_folders and email_obj.folder and email_obj.folder not in ["INBOX", "SENT", "DRAFTS", "TRASH"]:
                            try:
                                from ..services.folder_service import FolderService
                                folder_service = FolderService(email_service.imap_backend)
                                
                                # Create folder and all necessary parent folders
                                success = folder_service.create_folder(import_folder)
                                if success:
                                    folder_created = True
                                    print(f"Created folder: {import_folder}")
                                    # Re-select the newly created folder
                                    email_service.imap_backend.select_folder(import_folder)
                                else:
                                    raise Exception("Failed to create folder")
                                    
                            except Exception as create_error:
                                # If can't create custom folder, fall back to INBOX
                                print(f"Warning: Cannot create folder '{import_folder}': {str(create_error)}")
                                print(f"Importing email {email_obj.email_id} to INBOX instead")
                                import_folder = "INBOX"
                                email_service.imap_backend.select_folder(import_folder)
                        else:
                            # For system folders or when preserve_folders=False, fail if can't access
                            failed_count += 1
                            failed_reasons.append(f"Email {email_obj.email_id}: Cannot access folder '{import_folder}': {str(e)}")
                            continue
                    
                    # Convert EmailMessage back to raw email format if needed
                    if email_obj.raw_message:
                        # Use existing raw message
                        message_string = email_obj.raw_message.as_string()
                    else:
                        # Reconstruct email from EmailMessage data
                        message_string = _reconstruct_email_message(email_obj)
                    
                    # Import to IMAP server using APPEND command
                    success = email_service.imap_backend.append_message(
                        import_folder, 
                        message_string,
                        flags='\\Seen' if email_obj.is_read else ''
                    )
                    
                    if success:
                        success_count += 1
                        # Track folder statistics
                        if import_folder not in folder_stats:
                            folder_stats[import_folder] = 0
                        folder_stats[import_folder] += 1
                    else:
                        failed_count += 1
                        failed_reasons.append(f"Email {email_obj.email_id}: APPEND to '{import_folder}' failed")
                        
                except Exception as e:
                    failed_count += 1
                    failed_reasons.append(f"Email {email_obj.email_id}: {str(e)}")
            
            # Build result message
            result_msg = f"Successfully imported {success_count}/{len(imported_emails)} emails"
            
            if preserve_folders and len(folder_stats) > 1:
                result_msg += "\n\nImport breakdown by folder:"
                for folder, count in folder_stats.items():
                    result_msg += f"\n  - {folder}: {count} emails"
            elif folder_stats:
                folder_name = list(folder_stats.keys())[0]
                result_msg += f" to {folder_name}"
            
            if failed_count > 0:
                result_msg += f"\n\n{failed_count} emails failed to import:"
                for reason in failed_reasons[:5]:  # Show first 5 failures
                    result_msg += f"\n  - {reason}"
                if len(failed_reasons) > 5:
                    result_msg += f"\n  ... and {len(failed_reasons)-5} more"
            
            return result_msg
            
        except Exception as e:
            return f"Error importing emails: {str(e)}"
    
    @mcp.tool()
    async def download_attachment(email_id: str, attachment_filename: str) -> str:
        """Download email attachment to configured download path
        
        Args:
            email_id: Email ID containing the attachment
            attachment_filename: Name of attachment to download
        """
        try:
            email = email_service.imap_backend.fetch_email(email_id)
            
            # Find the attachment
            target_attachment = None
            for attachment in email.attachments:
                if attachment.filename == attachment_filename:
                    target_attachment = attachment
                    break
            
            if not target_attachment:
                return f"Attachment '{attachment_filename}' not found in email {email_id}"
            
            # Extract attachment data from raw message
            if not email.raw_message:
                return f"No raw message data available for email {email_id}"
            
            attachment_data = None
            for part in email.raw_message.walk():
                if part.get_filename() == attachment_filename:
                    attachment_data = part.get_payload(decode=True)
                    break
            
            if not attachment_data:
                return f"Could not extract attachment data for '{attachment_filename}'"
            
            # Save attachment
            from ..backends.file_backend import FileBackend
            from ..config import config_manager
            
            workspace_config = config_manager.workspace_config
            file_backend = FileBackend(
                email_export_path=workspace_config.email_export_path if workspace_config else None,
                attachment_download_path=workspace_config.attachment_download_path if workspace_config else None
            )
            
            saved_path = file_backend.save_attachment(attachment_data, attachment_filename)
            
            return f"Attachment '{attachment_filename}' saved to: {saved_path}"
            
        except Exception as e:
            return f"Error downloading attachment: {str(e)}"