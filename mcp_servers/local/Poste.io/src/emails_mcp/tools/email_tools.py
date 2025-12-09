import logging
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from ..services.email_service import EmailService
from ..utils.email_parser import format_email_summary


def register_email_tools(mcp: FastMCP, email_service: EmailService):
    """Register email-related MCP tools"""
    
    @mcp.tool()
    async def get_emails(folder: str = "INBOX", page: int = 1, page_size: int = 20) -> str:
        """Get paginated list of emails from specified folder
        
        Args:
            folder: Email folder name (default: INBOX)
            page: Page number starting from 1 (default: 1)
            page_size: Number of emails per page (default: 20)
        """
        try:
            result = email_service.get_emails(folder, page, page_size)
            
            if not result.emails:
                return f"Folder '{folder}' is empty or page {page} is out of range"
            
            output = f"Folder: {folder}\n"
            output += f"Page: {result.current_page}/{result.total_pages}\n"
            output += f"Total emails: {result.total_results}\n\n"
            
            for i, email in enumerate(result.emails, 1):
                output += f"{(result.current_page-1)*result.page_size + i}. "
                output += f"ID: {email.email_id}\n"
                output += f"   Subject: {email.subject}\n"
                output += f"   From: {email.from_addr}\n"
                output += f"   Date: {email.date}\n"
                if email.attachments:
                    output += f"   Attachments: {len(email.attachments)} files\n"
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"Error getting emails: {str(e)}"
    
    @mcp.tool()
    async def read_email(email_id: str) -> str:
        """Read full content of a specific email
        
        Args:
            email_id: Email ID to read
        """
        try:
            email = email_service.read_email(email_id)
            
            output = f"Email ID: {email.email_id}\n"
            output += f"Subject: {email.subject}\n"
            output += f"From: {email.from_addr}\n"
            output += f"To: {email.to_addr}\n"
            
            if email.cc_addr:
                output += f"CC: {email.cc_addr}\n"
            
            output += f"Date: {email.date}\n"
            output += f"Message-ID: {email.message_id}\n\n"
            
            if email.body_text:
                output += "Text Content:\n"
                output += f"{email.body_text}\n\n"
            
            if email.body_html:
                output += "HTML Content:\n"
                output += f"{email.body_html}\n\n"
            
            if email.attachments:
                output += "Attachments:\n"
                for i, att in enumerate(email.attachments, 1):
                    output += f"{i}. {att.filename} ({att.content_type}, {att.size} bytes)\n"
            
            return output
            
        except Exception as e:
            return f"Error reading email: {str(e)}"
    
    @mcp.tool()
    async def search_emails(query: str, folder: str = "INBOX", page: int = 1, page_size: int = 20) -> str:
        """Search emails with query string (sorted by date descending)
        
        Args:
            query: Search query (subject, from, body content)
            folder: Folder to search in (default: INBOX)
            page: Page number starting from 1 (default: 1)
            page_size: Number of results per page (default: 20)
        """
        try:
            result = email_service.search_emails(query, folder, page, page_size)
            
            if not result.emails:
                return f"No emails found matching query: {query}"
            
            output = f"Search query: {query}\n"
            output += f"Folder: {result.folder or 'current'}\n"
            output += f"Page: {result.current_page}/{result.total_pages}\n"
            output += f"Total results: {result.total_results}\n\n"
            
            for i, email in enumerate(result.emails, 1):
                output += f"{(result.current_page-1)*result.page_size + i}. "
                output += f"ID: {email.email_id}\n"
                output += f"   Subject: {email.subject}\n"
                output += f"   From: {email.from_addr}\n"
                output += f"   Date: {email.date}\n\n"
            
            return output
            
        except Exception as e:
            return f"Error searching emails: {str(e)}"
    
    @mcp.tool()
    async def send_email(to: str, subject: str, body: str, html_body: str = None,
                        cc: str = None, bcc: str = None, attachments: List[str] = None) -> str:
        """Send an email with optional HTML body, CC, BCC, and attachments
        
        Args:
            to: Recipient email address(es), comma-separated
            subject: Email subject
            body: Plain text body
            html_body: HTML body content (optional)
            cc: CC recipients, comma-separated (optional)
            bcc: BCC recipients, comma-separated (optional)
            attachments: List of file paths to attach (optional)
        """
        try:
            success = email_service.send_email(
                to=to,
                subject=subject,
                body=body,
                html_body=html_body,
                cc=cc,
                bcc=bcc,
                attachments=attachments
            )
            
            if success:
                attachment_info = f" with {len(attachments)} attachments" if attachments else ""
                return f"Email sent successfully to {to}{attachment_info}"
            else:
                return "Email sending failed"
                
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    @mcp.tool()
    async def reply_email(email_id: str, body: str, html_body: str = None,
                         cc: str = None, bcc: str = None, reply_all: bool = False) -> str:
        """Reply to an email
        
        Args:
            email_id: ID of email to reply to
            body: Reply message body (plain text)
            html_body: Reply message body (HTML, optional)
            cc: Additional CC recipients (optional)
            bcc: BCC recipients (optional)
            reply_all: Whether to reply to all recipients (default: False)
        """
        try:
            success = email_service.reply_email(
                email_id=email_id,
                body=body,
                html_body=html_body,
                cc=cc,
                bcc=bcc,
                reply_all=reply_all
            )
            
            if success:
                reply_type = "all recipients" if reply_all else "sender"
                return f"Reply sent successfully to {reply_type}"
            else:
                return "Reply sending failed"
                
        except Exception as e:
            return f"Error replying to email: {str(e)}"
    
    @mcp.tool()
    async def forward_email(email_id: str, to: str, body: str = None, html_body: str = None,
                           cc: str = None, bcc: str = None) -> str:
        """Forward an email to other recipients
        
        Args:
            email_id: ID of email to forward
            to: Recipients to forward to
            body: Additional message body (optional)
            html_body: Additional HTML message body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        """
        try:
            success = email_service.forward_email(
                email_id=email_id,
                to=to,
                body=body,
                html_body=html_body,
                cc=cc,
                bcc=bcc
            )
            
            if success:
                return f"Email forwarded successfully to {to}"
            else:
                return "Email forwarding failed"
                
        except Exception as e:
            return f"Error forwarding email: {str(e)}"
    
    @mcp.tool()
    async def delete_email(email_id: str) -> str:
        """Delete an email
        
        Args:
            email_id: Email ID to delete
        """
        try:
            success = email_service.delete_email(email_id)
            
            if success:
                return f"Email {email_id} deleted successfully"
            else:
                return "Email deletion failed"
                
        except Exception as e:
            return f"Error deleting email: {str(e)}"
    
    @mcp.tool()
    async def move_email(email_id: str, target_folder: str) -> str:
        """Move email to another folder
        
        Args:
            email_id: Email ID to move
            target_folder: Target folder name
        """
        try:
            success = email_service.move_email(email_id, target_folder)
            
            if success:
                return f"Email {email_id} moved to {target_folder} successfully"
            else:
                return "Email move failed"
                
        except Exception as e:
            return f"Error moving email: {str(e)}"
    
    @mcp.tool()
    async def mark_emails(email_ids: List[str], status: str) -> str:
        """Mark multiple emails with status (read/unread/important/not_important)
        
        Args:
            email_ids: List of email IDs to mark
            status: Status to set (read, unread, important, not_important)
        """
        try:
            if status not in ['read', 'unread', 'important', 'not_important']:
                return "Error: Status must be 'read', 'unread', 'important', or 'not_important'"
            
            success_count = email_service.mark_emails(email_ids, status)
            total_count = len(email_ids)
            
            return f"Successfully marked {success_count}/{total_count} emails as {status}"
            
        except Exception as e:
            return f"Error marking emails: {str(e)}"
    
    @mcp.tool()
    async def move_emails(email_ids: List[str], target_folder: str) -> str:
        """Move multiple emails to another folder with improved ID synchronization
        
        Args:
            email_ids: List of email IDs to move
            target_folder: Target folder name
        """
        try:
            success_count = 0
            failed_count = 0
            failed_ids = []
            
            # Sort email IDs in descending order to avoid ID renumbering issues
            # When emails are deleted/moved, higher IDs remain stable
            sorted_ids = sorted(email_ids, key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
            
            for email_id in sorted_ids:
                try:
                    # Verify email exists before attempting move
                    email_exists = email_service._check_email_exists(email_id)
                    if not email_exists:
                        logging.warning(f"Email {email_id} no longer exists, skipping")
                        failed_count += 1
                        failed_ids.append(email_id)
                        continue
                    
                    success = email_service.move_email(email_id, target_folder)
                    if success:
                        success_count += 1
                        logging.info(f"Successfully moved email {email_id}")
                    else:
                        failed_count += 1
                        failed_ids.append(email_id)
                        logging.warning(f"Failed to move email {email_id}")
                        
                except Exception as e:
                    failed_count += 1
                    failed_ids.append(email_id)
                    logging.error(f"Failed to move email {email_id}: {str(e)}")
            
            total_count = len(email_ids)
            result_msg = f"Successfully moved {success_count}/{total_count} emails to {target_folder}"
            
            if failed_count > 0:
                result_msg += f" ({failed_count} failed"
                if failed_ids:
                    result_msg += f": {', '.join(failed_ids[:5])}"  # Show first 5 failed IDs
                    if len(failed_ids) > 5:
                        result_msg += f" and {len(failed_ids)-5} more"
                result_msg += ")"
            
            return result_msg
            
        except Exception as e:
            return f"Error moving emails: {str(e)}"
    
    @mcp.tool()
    async def delete_emails(email_ids: List[str]) -> str:
        """Delete multiple emails with improved ID synchronization
        
        Args:
            email_ids: List of email IDs to delete
        """
        try:
            success_count = 0
            failed_count = 0
            failed_ids = []
            
            # Sort email IDs in descending order to avoid ID renumbering issues
            # When emails are deleted, higher IDs remain stable
            sorted_ids = sorted(email_ids, key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
            
            for email_id in sorted_ids:
                try:
                    # Verify email exists before attempting deletion
                    email_exists = email_service._check_email_exists(email_id)
                    if not email_exists:
                        logging.warning(f"Email {email_id} no longer exists, skipping")
                        failed_count += 1
                        failed_ids.append(email_id)
                        continue
                    
                    success = email_service.delete_email(email_id)
                    if success:
                        success_count += 1
                        logging.info(f"Successfully deleted email {email_id}")
                    else:
                        failed_count += 1
                        failed_ids.append(email_id)
                        logging.warning(f"Failed to delete email {email_id}")
                        
                except Exception as e:
                    failed_count += 1
                    failed_ids.append(email_id)
                    logging.error(f"Failed to delete email {email_id}: {str(e)}")
            
            total_count = len(email_ids)
            result_msg = f"Successfully deleted {success_count}/{total_count} emails"
            
            if failed_count > 0:
                result_msg += f" ({failed_count} failed"
                if failed_ids:
                    result_msg += f": {', '.join(failed_ids[:5])}"  # Show first 5 failed IDs
                    if len(failed_ids) > 5:
                        result_msg += f" and {len(failed_ids)-5} more"
                result_msg += ")"
            
            return result_msg
            
        except Exception as e:
            return f"Error deleting emails: {str(e)}"