# Emails MCP Server

A FastMCP-based email management server for IMAP/SMTP operations through the Model Context Protocol (MCP).

## Features

- 📧 **Email Management**: Get, read, search emails with pagination support
- 📤 **Send & Reply**: Send emails with HTML/text, attachments, CC/BCC support  
- 📁 **Folder Operations**: List, create, delete email folders
- 📋 **Draft Management**: Save, update, delete, and manage email drafts
- 📦 **Import/Export**: Backup/restore emails with folder structure preservation
- 🔗 **Attachment Handling**: Download email attachments to specified locations
- 📊 **Statistics**: Get mailbox statistics and unread counts
- 🛡️ **Security**: Workspace isolation and secure IMAP/SMTP connections

## Installation

### Uv is recommanded

```bash
uv tool install emails-mcp
```

### From source

```bash
git clone https://github.com/lockon-n/emails-mcp.git
cd emails-mcp
uv sync
```

## Usage

### Configuration

Create email configuration file (`/path/to/your/email/config.json`):

**Single account format:**
```json
{
    "email": "your-email@example.com",
    "password": "your-password", 
    "name": "Your Name",
    "imap_server": "imap.example.com",
    "imap_port": yourport (typically 993),
    "smtp_server": "smtp.example.com",
    "smtp_port": yourport (typically 587),
    "use_ssl": true/false,
    "use_starttls": true/false
}
```

### Usage with Claude Desktop

Add to your `~/.config/claude/claude_desktop_config.json` (Linux/macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

**Published Configuration:**
```json
{
  "mcpServers": {
    "emails-mcp": {
      "command": "uvx",
      "args": [
        "emails-mcp",
        "--config_file",
        "</path/to/your/email/config.json>",
        "--attachment_upload_path",
        "<your/upload/directory>",
        "--attachment_download_path",
        "<your/downloads/directory>",
        "--email_export_path",
        "<your/exports/directory>"
      ]
    }
  }
}
```

**Development/Unpublished Configuration:**
```json
{
  "mcpServers": {
    "emails-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "<path/to/emails-mcp>",
        "run",
        "emails-mcp",
        "--config_file", 
        "</path/to/your/email/config.json>",
        "--attachment_upload_path",
        "<your/upload/directory>",
        "--attachment_download_path",
        "<path/to/your/config.json>",
        "--email_export_path",
        "<your/exports/directory>"
      ]
    }
  }
}
```

**Note**: For security, this tool restricts file operations to the specified directories:
- `--attachment_upload_path`: Restricts attachment file selection 
- `--attachment_download_path`: Where downloaded attachments are saved
- `--email_export_path`: Where email exports are saved

### As a command line tool

```bash
# Basic usage (uses default config file: test_emils.json)
emails-mcp

# With custom configuration file
emails-mcp --config_file config.json

# With path restrictions for security
emails-mcp --config_file config.json \
  --attachment_download_path ./downloads \
  --email_export_path ./exports \
  --attachment_upload_path ./uploads

# With debug logging
emails-mcp --config_file config.json --debug
```

#### Supported Arguments

- `--config_file`: Email configuration file path
- `--attachment_upload_path`: Directory for attachment uploads (restricts file selection)
- `--attachment_download_path`: Directory for attachment downloads (files saved here)
- `--email_export_path`: Directory for email exports (exports saved here)
- `--debug`: Enable debug logging

## Available Tools

<details>
<summary><strong>📧 Email Operations</strong></summary>

### get_emails
Get paginated list of emails from specified folder
- `folder`: Email folder name (default: "INBOX")
- `page`: Page number starting from 1 (default: 1)
- `page_size`: Number of emails per page (default: 20)

### read_email
Read full content of a specific email
- `email_id`: Email ID to read

### search_emails
Search emails with query string (sorted by date descending)
- `query`: Search query (subject, from, body content)
- `folder`: Folder to search in (optional)
- `page`: Page number starting from 1 (default: 1)
- `page_size`: Number of results per page (default: 20)

### send_email
Send an email with optional HTML body, CC, BCC, and attachments
- `to`: Recipient email address(es), comma-separated
- `subject`: Email subject
- `body`: Plain text body
- `html_body`: HTML body content (optional)
- `cc`: CC recipients, comma-separated (optional)
- `bcc`: BCC recipients, comma-separated (optional)
- `attachments`: List of file paths to attach (optional)

### reply_email
Reply to an email
- `email_id`: ID of email to reply to
- `body`: Reply message body (plain text)
- `html_body`: Reply message body (HTML, optional)
- `cc`: Additional CC recipients (optional)
- `bcc`: BCC recipients (optional)
- `reply_all`: Whether to reply to all recipients (default: False)

### forward_email
Forward an email to other recipients
- `email_id`: ID of email to forward
- `to`: Recipients to forward to
- `body`: Additional message body (optional)
- `html_body`: Additional HTML message body (optional)
- `cc`: CC recipients (optional)
- `bcc`: BCC recipients (optional)

### delete_email / delete_emails
Delete single or multiple emails
- `email_id`: Email ID to delete (single)
- `email_ids`: List of email IDs to delete (batch)

### move_email / move_emails
Move single or multiple emails to another folder
- `email_id`: Email ID to move (single)
- `email_ids`: List of email IDs to move (batch)
- `target_folder`: Target folder name

### mark_emails
Mark multiple emails with status
- `email_ids`: List of email IDs to mark
- `status`: Status to set (read, unread, important, not_important)

</details>

<details>
<summary><strong>📁 Folder Operations</strong></summary>

### get_folders
Get list of available email folders

### create_folder
Create new email folder
- `folder_name`: Name of folder to create

### delete_folder
Delete email folder
- `folder_name`: Name of folder to delete

### get_mailbox_stats
Get mailbox statistics
- `folder_name`: Specific folder name (optional, defaults to all folders)

### get_unread_count
Get unread message count
- `folder_name`: Specific folder name (optional, defaults to all folders)

</details>

<details>
<summary><strong>📋 Draft Management</strong></summary>

### save_draft
Save email draft
- `subject`: Email subject
- `body`: Plain text body
- `html_body`: HTML body content (optional)
- `to`: Recipient email address(es) (optional)
- `cc`: CC recipients (optional)
- `bcc`: BCC recipients (optional)

### get_drafts
Get list of saved drafts
- `page`: Page number starting from 1 (default: 1)
- `page_size`: Number of drafts per page (default: 20)

### update_draft
Update existing draft
- `draft_id`: Draft ID to update
- `subject`: Email subject (optional)
- `body`: Plain text body (optional)
- `html_body`: HTML body content (optional)
- `to`: Recipient email address(es) (optional)
- `cc`: CC recipients (optional)
- `bcc`: BCC recipients (optional)

### delete_draft
Delete draft
- `draft_id`: Draft ID to delete

</details>

<details>
<summary><strong>🔧 Management & Utilities</strong></summary>

### check_connection
Check email server connection status

### get_email_headers
Get complete email headers for technical analysis
- `email_id`: Email ID to get headers for

### export_emails
Export emails to file for backup
- `folder`: Specific folder to export (optional)
- `export_path`: Path where to save the export file (default: "emails_export.json")
- `max_emails`: Maximum number of emails to export (optional)
- `export_all_folders`: Export from all folders instead of just one (default: False)

### import_emails
Import emails from backup file to IMAP server
- `import_path`: Path to import file
- `target_folder`: Target folder for imported emails (if preserve_folders=False)
- `preserve_folders`: Whether to preserve original folder structure (default: True)

### download_attachment
Download email attachment to specified path
- `email_id`: Email ID containing the attachment
- `attachment_filename`: Name of attachment to download
- `download_path`: Directory path where to save the attachment

</details>

## Configuration Options

### Email Server Settings
- **IMAP/SMTP servers**: Configure your email provider's servers
- **Security**: Supports SSL/TLS and STARTTLS
- **Authentication**: Standard username/password authentication

### Workspace Security
- **Path Restriction**: Limit file operations to specified directory
- **Path Validation**: All file paths are validated for security

### Pagination
- **Default page size**: 20 items per page
- **Maximum page size**: 50 items per page
- **Auto-correction**: Invalid page parameters are automatically corrected

## Error Handling

The server includes comprehensive error handling:
- **Connection errors**: Graceful handling of network issues
- **Authentication errors**: Clear error messages for login failures
- **Validation errors**: Input validation with helpful error messages
- **File system errors**: Proper handling of file operation failures

## Security Considerations

- **Workspace isolation**: File operations can be restricted to a safe directory
- **Input validation**: All user inputs are validated
- **Connection security**: Supports SSL/TLS encryption
- **Error messages**: Avoid exposing sensitive information in error messages

## Development

### Build

```bash
uv build
```

### Publish to PyPI

```bash
uv publish
```

### Local Development

```bash
# Install development dependencies
uv sync

# Run tests
uv run python -m pytest

# Run server
uv run python -m emails_mcp.server
```

### Project Structure
The codebase follows software engineering best practices:

```
- models/          # Data models and configurations
- config/          # Configuration management  
- utils/           # Utilities, validators, and parsers
- backends/        # IMAP, SMTP, and file operation backends
- services/        # Business logic layer
- tools/           # MCP tool definitions
- server.py        # Main MCP server entry point
```

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!