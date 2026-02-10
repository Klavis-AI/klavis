from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.email import EmailMessage
from ..backends.file_backend import FileBackend
from ..utils.exceptions import EmailMCPError


class DraftService:
    """Draft management service layer"""
    
    def __init__(self, file_backend: FileBackend):
        self.file_backend = file_backend
        self.drafts: Dict[str, Dict[str, Any]] = {}
        self._draft_counter = 1
    
    def save_draft(self, subject: str, body: str, 
                   html_body: Optional[str] = None,
                   to: Optional[str] = None,
                   cc: Optional[str] = None,
                   bcc: Optional[str] = None) -> str:
        """Save email draft and return draft ID"""
        try:
            draft_id = f"draft_{self._draft_counter}"
            self._draft_counter += 1
            
            draft_data = {
                'draft_id': draft_id,
                'subject': subject,
                'body': body,
                'html_body': html_body,
                'to': to,
                'cc': cc,
                'bcc': bcc,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.drafts[draft_id] = draft_data
            return draft_id
            
        except Exception as e:
            raise EmailMCPError(f"Failed to save draft: {str(e)}")
    
    def get_drafts(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get paginated list of drafts"""
        try:
            draft_list = list(self.drafts.values())
            draft_list.sort(key=lambda x: x['updated_at'], reverse=True)
            
            total_drafts = len(draft_list)
            total_pages = (total_drafts + page_size - 1) // page_size if total_drafts > 0 else 1
            
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_drafts = draft_list[start_idx:end_idx]
            
            return {
                'drafts': page_drafts,
                'total_drafts': total_drafts,
                'current_page': page,
                'total_pages': total_pages,
                'page_size': page_size
            }
            
        except Exception as e:
            raise EmailMCPError(f"Failed to get drafts: {str(e)}")
    
    def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """Get specific draft by ID"""
        if draft_id not in self.drafts:
            raise EmailMCPError(f"Draft not found: {draft_id}")
        
        return self.drafts[draft_id]
    
    def update_draft(self, draft_id: str, 
                    subject: Optional[str] = None,
                    body: Optional[str] = None,
                    html_body: Optional[str] = None,
                    to: Optional[str] = None,
                    cc: Optional[str] = None,
                    bcc: Optional[str] = None) -> bool:
        """Update existing draft"""
        if draft_id not in self.drafts:
            raise EmailMCPError(f"Draft not found: {draft_id}")
        
        try:
            draft = self.drafts[draft_id]
            
            # Update only provided fields
            if subject is not None:
                draft['subject'] = subject
            if body is not None:
                draft['body'] = body
            if html_body is not None:
                draft['html_body'] = html_body
            if to is not None:
                draft['to'] = to
            if cc is not None:
                draft['cc'] = cc
            if bcc is not None:
                draft['bcc'] = bcc
            
            draft['updated_at'] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            raise EmailMCPError(f"Failed to update draft: {str(e)}")
    
    def delete_draft(self, draft_id: str) -> bool:
        """Delete draft"""
        if draft_id not in self.drafts:
            raise EmailMCPError(f"Draft not found: {draft_id}")
        
        try:
            del self.drafts[draft_id]
            return True
        except Exception as e:
            raise EmailMCPError(f"Failed to delete draft: {str(e)}")
    
    def export_drafts(self, export_path: str) -> bool:
        """Export all drafts to file"""
        try:
            # Convert drafts to list for export
            draft_emails = []
            for draft_data in self.drafts.values():
                # Create minimal EmailMessage for export
                email_obj = EmailMessage(
                    email_id=draft_data['draft_id'],
                    subject=draft_data['subject'],
                    from_addr="",  # Will be set when sending
                    to_addr=draft_data.get('to', ''),
                    cc_addr=draft_data.get('cc'),
                    bcc_addr=draft_data.get('bcc'),
                    body_text=draft_data['body'],
                    body_html=draft_data.get('html_body'),
                    folder="Drafts"
                )
                draft_emails.append(email_obj)
            
            return self.file_backend.export_emails(draft_emails, export_path, 'json')
            
        except Exception as e:
            raise EmailMCPError(f"Failed to export drafts: {str(e)}")
    
    def import_drafts(self, import_path: str) -> int:
        """Import drafts from file"""
        try:
            imported_emails = self.file_backend.import_emails(import_path)
            imported_count = 0
            
            for email_obj in imported_emails:
                # Convert EmailMessage back to draft format
                self.save_draft(
                    subject=email_obj.subject,
                    body=email_obj.body_text or "",
                    html_body=email_obj.body_html,
                    to=email_obj.to_addr,
                    cc=email_obj.cc_addr,
                    bcc=email_obj.bcc_addr
                )
                imported_count += 1
            
            return imported_count
            
        except Exception as e:
            raise EmailMCPError(f"Failed to import drafts: {str(e)}")