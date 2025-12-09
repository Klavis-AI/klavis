import argparse
import logging
import sys
import os
from mcp.server.fastmcp import FastMCP
from .config import config_manager
from .services import EmailService, FolderService, SearchService, DraftService
from .backends import IMAPBackend, SMTPBackend, FileBackend
from .tools import register_email_tools, register_folder_tools, register_management_tools


def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )


def create_services(email_config):
    """Create service instances"""
    # Create backends
    imap_backend = IMAPBackend(email_config)
    smtp_backend = SMTPBackend(email_config)
    
    email_export_path = config_manager.workspace_config.email_export_path if config_manager.workspace_config else None
    attachment_download_path = config_manager.workspace_config.attachment_download_path if config_manager.workspace_config else None
    file_backend = FileBackend(email_export_path, attachment_download_path)
    
    # Create services
    email_service = EmailService(email_config)
    folder_service = FolderService(imap_backend)
    search_service = SearchService(imap_backend)
    draft_service = DraftService(file_backend)
    
    return email_service, folder_service, search_service, draft_service


def main():
    """Main function to run the emails MCP server"""
    parser = argparse.ArgumentParser(description='Emails MCP Server')
    parser.add_argument(
        '--attachment_upload_path', 
        type=str, 
        default=None,
        help='Directory path for attachment uploads (restricts file selection to this path and subdirectories)'
    )
    parser.add_argument(
        '--attachment_download_path', 
        type=str, 
        default=None,
        help='Directory path for attachment downloads (files will be saved here with unique names)'
    )
    parser.add_argument(
        '--email_export_path', 
        type=str, 
        default=None,
        help='Directory path for email exports (exports will be saved here with date-based filenames)'
    )
    parser.add_argument(
        '--config_file', 
        type=str, 
        default='test_emils.json',
        help='Email configuration file path'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize MCP server
        mcp = FastMCP("emails-mcp")
        
        # Load configuration
        config_manager.load_workspace_config(
            attachment_upload_path=args.attachment_upload_path,
            attachment_download_path=args.attachment_download_path, 
            email_export_path=args.email_export_path,
            config_file=args.config_file
        )
        
        if not os.path.exists(args.config_file):
            logger.error(f"Configuration file not found: {args.config_file}")
            sys.exit(1)
        
        email_config = config_manager.load_email_config(args.config_file)
        if not email_config:
            logger.error("No valid email configuration found")
            sys.exit(1)
        
        logger.info(f"Loaded configuration for: {email_config.email}")
        
        # Create services
        email_service, folder_service, search_service, draft_service = create_services(email_config)
        
        # Register MCP tools
        register_email_tools(mcp, email_service)
        register_folder_tools(mcp, folder_service)
        register_management_tools(mcp, draft_service, email_service)
        
        logger.info("All MCP tools registered successfully")
        
        # Log path restrictions if set
        if config_manager.workspace_config:
            config = config_manager.workspace_config
            if config.attachment_upload_path:
                logger.info(f"Attachment uploads restricted to: {config.attachment_upload_path}")
            if config.attachment_download_path:
                logger.info(f"Attachment downloads will be saved to: {config.attachment_download_path}")
            if config.email_export_path:
                logger.info(f"Email exports will be saved to: {config.email_export_path}")
        
        # Test connection on startup
        try:
            imap_ok, smtp_ok = email_service.check_connection()
            if imap_ok and smtp_ok:
                logger.info("All email connections verified successfully")
            elif imap_ok:
                logger.warning("IMAP connected, but SMTP connection failed")
            elif smtp_ok:
                logger.warning("SMTP connected, but IMAP connection failed") 
            else:
                logger.warning("Both IMAP and SMTP connections failed - check configuration")
        except Exception as e:
            logger.warning(f"Connection test failed: {str(e)}")
        
        # Start the MCP server
        logger.info("Starting emails MCP server...")
        mcp.run(transport='stdio')
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            if 'email_service' in locals():
                email_service.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()