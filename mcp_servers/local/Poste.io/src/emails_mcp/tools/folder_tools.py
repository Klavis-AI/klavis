from mcp.server.fastmcp import FastMCP
from ..services.folder_service import FolderService


def register_folder_tools(mcp: FastMCP, folder_service: FolderService):
    """Register folder-related MCP tools"""
    
    @mcp.tool()
    async def get_folders() -> str:
        """Get list of available email folders"""
        try:
            folders = folder_service.get_folders()
            
            if not folders:
                return "No folders found"
            
            output = "Available folders:\n"
            for i, folder in enumerate(folders, 1):
                output += f"{i}. {folder.name}"
                if folder.can_select:
                    output += f" ({folder.total_messages} total, {folder.unread_messages} unread)"
                else:
                    output += " (cannot select)"
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"Error getting folders: {str(e)}"
    
    @mcp.tool()
    async def create_folder(folder_name: str) -> str:
        """Create new email folder
        
        Args:
            folder_name: Name of folder to create
        """
        try:
            success = folder_service.create_folder(folder_name)
            
            if success:
                return f"Folder '{folder_name}' created successfully"
            else:
                return f"Failed to create folder '{folder_name}'"
                
        except Exception as e:
            return f"Error creating folder: {str(e)}"
    
    @mcp.tool()
    async def delete_folder(folder_name: str) -> str:
        """Delete email folder
        
        Args:
            folder_name: Name of folder to delete
        """
        try:
            success = folder_service.delete_folder(folder_name)
            
            if success:
                return f"Folder '{folder_name}' deleted successfully"
            else:
                return f"Failed to delete folder '{folder_name}'"
                
        except Exception as e:
            return f"Error deleting folder: {str(e)}"
    
    @mcp.tool()
    async def get_mailbox_stats(folder_name: str = None) -> str:
        """Get mailbox statistics
        
        Args:
            folder_name: Specific folder name (optional, defaults to all folders)
        """
        try:
            if folder_name:
                stats = folder_service.get_folder_stats(folder_name)
                output = f"Folder Statistics for '{stats.folder_name}':\n"
                output += f"Total messages: {stats.total_messages}\n"
                output += f"Unread messages: {stats.unread_messages}\n"
                if stats.total_size_mb:
                    output += f"Total size: {stats.total_size_mb:.2f} MB\n"
            else:
                folders = folder_service.get_folders()
                output = "Mailbox Statistics:\n"
                total_messages = 0
                total_unread = 0
                
                for folder in folders:
                    if folder.can_select:
                        output += f"  {folder.name}: {folder.total_messages} total, {folder.unread_messages} unread\n"
                        total_messages += folder.total_messages
                        total_unread += folder.unread_messages
                
                output += f"\nOverall Total: {total_messages} messages, {total_unread} unread\n"
            
            return output
            
        except Exception as e:
            return f"Error getting mailbox stats: {str(e)}"
    
    @mcp.tool()
    async def get_unread_count(folder_name: str = None) -> str:
        """Get unread message count
        
        Args:
            folder_name: Specific folder name (optional, defaults to all folders)
        """
        try:
            unread_count = folder_service.get_unread_count(folder_name)
            
            if folder_name:
                return f"Unread messages in '{folder_name}': {unread_count}"
            else:
                return f"Total unread messages: {unread_count}"
                
        except Exception as e:
            return f"Error getting unread count: {str(e)}"