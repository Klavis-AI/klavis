# Dropbox MCP Server

A Model Context Protocol (MCP) server for Dropbox integration, providing comprehensive file management capabilities.

## Features

### File & Folder Operations
- **List Folder**: Browse folder contents with optional recursive listing
- **Create Folder**: Create new folders with auto-rename support
- **Delete File/Folder**: Permanently delete files and folders
- **Move File/Folder**: Move or rename files and folders
- **Copy File/Folder**: Create copies of files and folders

### File Content Operations
- **Upload File**: Upload local files directly using `file://` URIs for efficient binary transfer
- **Download File**: Download files with base64 encoded content
- **Get File Info**: Retrieve detailed metadata about files and folders

### File Version Management
- **List Revisions**: View file revision history
- **Restore File**: Restore files to previous versions

### Search & Discovery
- **Search Files**: Search across your Dropbox with advanced filters
- **Get Shared Links**: List existing shared links
- **Share File**: Create shared links with customizable settings

### Advanced Sharing & Collaboration
- **Add File Member**: Add collaborators to specific files
- **List File Members**: View who has access to files
- **Remove File Member**: Remove collaborators from files
- **Share Folder**: Share folders with team members
- **List Folder Members**: View shared folder collaborators
- **Add Folder Member**: Add members to shared folders

### Account & Utilities
- **Get Current Account**: Retrieve current user account information
- **Get Space Usage**: Check storage space usage and allocation
- **Get Temporary Link**: Generate temporary download links

## Prerequisites

### Dropbox App Permissions

Before using this MCP server, you need to create a Dropbox app at [https://www.dropbox.com/developers/apps](https://www.dropbox.com/developers/apps) with the following permissions:

#### Account Info
- **account_info.read** - View basic information about your Dropbox account such as your username, email, and country

#### Files and Folders
- **files.metadata.write** - View and edit information about your Dropbox files and folders
- **files.metadata.read** - View information about your Dropbox files and folders
- **files.content.write** - Edit content of your Dropbox files and folders
- **files.content.read** - View content of your Dropbox files and folders

#### Collaboration
- **sharing.write** - View and manage your Dropbox sharing settings and collaborators
- **sharing.read** - View your Dropbox sharing settings and collaborators
- **file_requests.write** - View and manage your Dropbox file requests
- **file_requests.read** - View your Dropbox file requests
- **contacts.write** - View and manage your manually added Dropbox contacts
- **contacts.read** - View your manually added Dropbox contacts

> **Note**: These permissions are required for the server to provide full functionality. Some features may not work if certain permissions are not granted.

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and configure your Dropbox credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Dropbox app credentials:

```bash
# Dropbox API Configuration
DROPBOX_APP_KEY=your_app_key_here
DROPBOX_APP_SECRET=your_app_secret_here
DROPBOX_ACCESS_TOKEN=your_access_token_here
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start the Server

```bash
npm start
```

The server will validate your Dropbox connection on startup and display your account information.

### 4. Use as HTTP Server

Make requests with your access token (either from environment or header):

```bash
curl -X POST http://localhost:5000/mcp \
  -H "Content-Type: application/json" \
  -H "x-auth-token: YOUR_DROPBOX_ACCESS_TOKEN" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### 5. Use as MCP Server

Add to your MCP client configuration:

```json
{
  "servers": {
    "dropbox": {
      "command": "node",
      "args": ["path/to/dropbox/mcp/server/dist/index.js"]
    }
  }
}
```

## Available Tools

### list_folder
List contents of a folder
```typescript
{
  path: string (optional, default: ""), // Folder path
  recursive: boolean (optional, default: false),
  include_media_info: boolean (optional, default: false),
  include_deleted: boolean (optional, default: false),
  include_has_explicit_shared_members: boolean (optional, default: false),
  limit: number (optional)
}
```

### create_folder
Create a new folder
```typescript
{
  path: string, // Folder path to create
  autorename: boolean (optional, default: false)
}
```

### delete_file
Delete a file or folder
```typescript
{
  path: string // Path of file/folder to delete
}
```

### move_file
Move or rename a file/folder
```typescript
{
  from_path: string, // Current path
  to_path: string, // New path
  allow_shared_folder: boolean (optional, default: false),
  autorename: boolean (optional, default: false),
  allow_ownership_transfer: boolean (optional, default: false)
}
```

### copy_file
Copy a file or folder
```typescript
{
  from_path: string, // Source path
  to_path: string, // Destination path
  allow_shared_folder: boolean (optional, default: false),
  autorename: boolean (optional, default: false),
  allow_ownership_transfer: boolean (optional, default: false)
}
```

### search_files
Search for files and folders
```typescript
{
  query: string, // Search query
  path: string (optional, default: ""), // Path to search within
  max_results: number (optional, default: 100),
  file_status: "active" | "deleted" (optional, default: "active"),
  filename_only: boolean (optional, default: false)
}
```

### get_file_info
Get detailed information about a file or folder
```typescript
{
  path: string, // File/folder path
  include_media_info: boolean (optional, default: false),
  include_deleted: boolean (optional, default: false),
  include_has_explicit_shared_members: boolean (optional, default: false)
}
```

### share_file
Create a shared link
```typescript
{
  path: string, // File/folder path to share
  settings: {
    requested_visibility: "public" | "team_only" | "password" (optional),
    link_password: string (optional),
    expires: string (optional) // ISO 8601 format
  } (optional)
}
```

### get_shared_links
List shared links
```typescript
{
  path: string (optional), // Specific path to get links for
  cursor: string (optional) // Pagination cursor
}
```

### upload_file
Upload a local file to Dropbox
```typescript
{
  dropbox_path: string, // Upload path in Dropbox (e.g., "/folder/filename.txt")
  local_file_uri: string, // Local file URI (e.g., "file:///home/user/documents/file.txt")
  mode: "add" | "overwrite" | "update" (optional, default: "add"),
  autorename: boolean (optional, default: false),
  mute: boolean (optional, default: false)
}
// Note: local_file_uri must use the file:// protocol and point to an existing local file
```

### download_file
Download a file
```typescript
{
  path: string // File path to download
}
```

### list_revisions
List file revisions/versions
```typescript
{
  path: string, // File path
  mode: "path" | "id" (optional, default: "path"),
  limit: number (optional, default: 10)
}
```

### restore_file
Restore a file to a previous version
```typescript
{
  path: string, // File path
  rev: string // Revision ID to restore to
}
```

### get_current_account
Get current user account information
```typescript
{} // No parameters required
```

### get_space_usage
Get storage space usage
```typescript
{} // No parameters required
```

### get_temporary_link
Get a temporary download link
```typescript
{
  path: string // File path
}
```

### add_file_member
Add collaborator to a file
```typescript
{
  file: string, // File path
  members: [{
    email: string, // Member email
    access_level: "viewer" | "editor" (optional, default: "viewer")
  }],
  quiet: boolean (optional, default: false),
  custom_message: string (optional)
}
```

### list_file_members
List file collaborators
```typescript
{
  file: string, // File path
  include_inherited: boolean (optional, default: true),
  limit: number (optional, default: 100)
}
```

### remove_file_member
Remove collaborator from file
```typescript
{
  file: string, // File path
  member: string // Member email to remove
}
```

### share_folder
Share a folder
```typescript
{
  path: string, // Folder path
  member_policy: "team" | "anyone" (optional, default: "anyone"),
  acl_update_policy: "owner" | "editors" (optional, default: "owner"),
  shared_link_policy: "anyone" | "members" (optional, default: "anyone"),
  force_async: boolean (optional, default: false)
}
```

### list_folder_members
List shared folder members
```typescript
{
  shared_folder_id: string, // Shared folder ID
  limit: number (optional, default: 100)
}
```

### add_folder_member
Add member to shared folder
```typescript
{
  shared_folder_id: string, // Shared folder ID
  members: [{
    email: string, // Member email
    access_level: "viewer" | "editor" | "owner" (optional, default: "viewer")
  }],
  quiet: boolean (optional, default: false),
  custom_message: string (optional)
}
```

### list_folder_continue
Continue listing folder contents using cursor
```typescript
{
  cursor: string // Cursor from previous list_folder operation
}
```

### list_shared_folders
List all shared folders
```typescript
{
  cursor: string (optional), // Pagination cursor
  limit: number (optional, default: 100)
}
```

### unshare_file
Remove all members from a file
```typescript
{
  file: string // File ID or path
}
```

### unshare_folder
Unshare a folder (owner only)
```typescript
{
  shared_folder_id: string, // Shared folder ID
  leave_a_copy: boolean (optional, default: false)
}
```

### create_file_request
Create a file request for others to upload files
```typescript
{
  title: string, // Request title
  destination: string, // Upload destination path
  description: string (optional)
}
```

### get_file_request
Get file request details
```typescript
{
  id: string // File request ID
}
```

### list_file_requests
List all file requests
```typescript
{} // No parameters required
```

### delete_file_request
Delete file requests
```typescript
{
  ids: string[] // Array of file request IDs to delete
}
```

### update_file_request
Update file request settings
```typescript
{
  id: string, // File request ID
  title: string (optional), // New title
  destination: string (optional), // New destination
  description: string (optional), // New description
  open: boolean (optional) // Open/close the request
}
```

### batch_delete
Delete multiple files/folders efficiently
```typescript
{
  entries: [{
    path: string // File/folder path to delete
  }] // Up to 1000 entries
}
```

### batch_move
Move multiple files/folders efficiently
```typescript
{
  entries: [{
    from_path: string, // Current path
    to_path: string // New path
  }], // Up to 1000 entries
  autorename: boolean (optional, default: false),
  allow_ownership_transfer: boolean (optional, default: false)
}
```

### batch_copy
Copy multiple files/folders efficiently
```typescript
{
  entries: [{
    from_path: string, // Source path
    to_path: string // Destination path
  }], // Up to 1000 entries
  autorename: boolean (optional, default: false)
}
```

### check_batch_job_status
Check status of batch operations
```typescript
{
  async_job_id: string // Job ID from batch operation
}
```

### get_thumbnail
Get file thumbnail
```typescript
{
  path: string, // File path
  format: "jpeg" | "png" (optional, default: "jpeg"),
  size: "w32h32" | "w64h64" | "w128h128" | "w256h256" | "w480h320" | "w640h480" | "w960h640" | "w1024h768" | "w2048h1536" (optional, default: "w256h256")
}
```

### add_file_properties
Add custom properties to a file
```typescript
{
  path: string, // File path
  property_groups: [{
    template_id: string, // Property template ID
    fields: [{
      name: string, // Property field name
      value: string // Property field value
    }]
  }]
}
```

### overwrite_file_properties
Overwrite all custom properties on a file
```typescript
{
  path: string, // File path
  property_groups: [{
    template_id: string, // Property template ID
    fields: [{
      name: string, // Property field name
      value: string // Property field value
    }]
  }]
}
```

### update_file_properties
Update specific custom properties on a file
```typescript
{
  path: string, // File path
  update_property_groups: [{
    template_id: string, // Property template ID
    add_or_update_fields: [{
      name: string, // Property field name
      value: string // Property field value
    }] (optional),
    remove_fields: string[] (optional) // Field names to remove
  }]
}
```

### remove_file_properties
Remove custom properties from a file
```typescript
{
  path: string, // File path
  property_template_ids: string[] // Template IDs to remove
}
```

### search_file_properties
Search files by custom properties
```typescript
{
  queries: [{
    query: string, // Search query
    mode: "field_name" | "field_value", // Search mode
    logical_operator: "or_operator" (optional)
  }],
  template_filter: "filter_none" | "filter_some" (optional, default: "filter_none")
}
```

### list_property_templates
List available property templates
```typescript
{} // No parameters required
```

### get_property_template
Get property template details
```typescript
{
  template_id: string // Template ID
}
```

### save_url
Save content from URL to Dropbox
```typescript
{
  path: string, // Save path
  url: string // URL to download and save
}
```

### save_url_check_job_status
Check status of URL save operation
```typescript
{
  async_job_id: string // Job ID from save_url operation
}
```

### lock_file_batch
Lock files to prevent editing
```typescript
{
  entries: [{
    path: string // File path to lock
  }] // Up to 1000 entries
}
```

### unlock_file_batch
Unlock previously locked files
```typescript
{
  entries: [{
    path: string // File path to unlock
  }] // Up to 1000 entries
}
```

### list_received_files
List files shared with you by others
```typescript
{
  cursor: string (optional), // Pagination cursor
  limit: number (optional, default: 100)
}
```

### check_job_status
Check status of asynchronous operations
```typescript
{
  async_job_id: string // Job ID from async operation
}
```

## Authentication & Setup

### Obtaining Dropbox Credentials

To use this MCP server, you need to create a Dropbox app and obtain API credentials:

#### 1. Create a Dropbox App

1. Go to the [Dropbox Developer Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose "Scoped access" as the API
4. Choose "Full Dropbox" or "App folder" depending on your needs
5. Give your app a name
6. Click "Create app"

#### 2. Get Your App Key and App Secret

1. In your app's settings page, find the "App key" and "App secret"
2. Copy these values for your `.env` file

#### 3. Generate an Access Token

**Option A: Generate via Developer Console (Quick)**
1. In your app's settings, scroll to "OAuth 2" section
2. Click "Generate" under "Generated access token"
3. Copy the generated token

**Option B: OAuth Flow (Production)**
1. Implement the OAuth 2.0 flow in your application
2. Use the authorization URL format:
   ```
   https://www.dropbox.com/oauth2/authorize?client_id=YOUR_APP_KEY&response_type=code&redirect_uri=YOUR_REDIRECT_URI
   ```
3. Exchange the authorization code for an access token:
   ```bash
   curl -X POST https://api.dropboxapi.com/oauth2/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "code=AUTHORIZATION_CODE&grant_type=authorization_code&client_id=YOUR_APP_KEY&client_secret=YOUR_APP_SECRET&redirect_uri=YOUR_REDIRECT_URI"
   ```

#### 4. Set Permissions

In your app settings, under "Permissions", ensure you have the necessary scopes enabled:
- `files.metadata.write` - For file operations
- `files.content.write` - For uploading/downloading files
- `sharing.write` - For sharing operations
- `account_info.read` - For account information

### Environment Configuration

Create a `.env` file in the server directory:

```bash
# Required: Dropbox API Configuration
DROPBOX_APP_KEY=your_app_key_here
DROPBOX_APP_SECRET=your_app_secret_here
DROPBOX_ACCESS_TOKEN=your_access_token_here

# Optional: Server Configuration
PORT=5000
```

### Token Authentication

The server supports multiple ways to provide the access token:

1. **Environment Variable**: Set `DROPBOX_ACCESS_TOKEN` in `.env`
2. **HTTP Header**: Pass `x-auth-token` header in HTTP requests
3. **Runtime Configuration**: The server will use environment token as fallback

### Security Notes

- Keep your App Secret secure and never expose it in client-side code
- Access tokens should be stored securely
- Consider implementing token refresh for production applications
- Use HTTPS in production environments

## Error Handling

The server provides detailed error messages for common issues:
- Invalid access tokens
- File not found errors
- Permission denied errors
- Rate limiting responses

## Troubleshooting

### Common Issues

#### 401 Authentication Error
If you get a "Response failed with a 401 code" error:

1. **Check Token Expiration**: Access tokens generated via the Developer Console have a limited lifespan (typically 4 hours)
2. **Regenerate Token**: Go to your [Dropbox Developer Console](https://www.dropbox.com/developers/apps), find your app, and generate a new access token
3. **Update .env File**: Replace the `DROPBOX_ACCESS_TOKEN` value in your `.env` file
4. **Restart Server**: After updating the token, restart the server

#### Token Generation Steps
1. Visit [Dropbox Developer Console](https://www.dropbox.com/developers/apps)
2. Click on your app name
3. Scroll to "OAuth 2" section
4. Click "Generate" under "Generated access token"
5. Copy the new token to your `.env` file

#### Environment Variables Not Loading
- Ensure `.env` file is in the same directory as your server
- Check that `dotenv` is properly installed and imported
- Verify there are no syntax errors in your `.env` file

#### Permission Errors
- Check that your app has the necessary scopes enabled in the Developer Console
- Ensure your account has the required permissions for the operations you're trying to perform

### Testing the Connection

You can test your Dropbox connection with a simple curl command:

```bash
curl -X POST https://api.dropboxapi.com/2/users/get_current_account \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Implementation Notes

### File Upload with file:// URIs

This implementation follows the [MCP Resource concept](https://modelcontextprotocol.io/docs/concepts/resources) by using `file://` URIs for local file uploads. This approach provides several benefits:

- **Direct Binary Transfer**: Files are read directly from the local filesystem as binary data
- **No Encoding Overhead**: Eliminates the need for base64 encoding/decoding
- **Memory Efficient**: Streams file content without loading entire files into memory as text
- **Type Preservation**: Maintains original file type and binary integrity
- **Filesystem Integration**: Natural integration with local file operations

The `upload_file` tool now requires:
- `dropbox_path`: Destination path in Dropbox
- `local_file_uri`: Local file URI using `file://` protocol (e.g., `file:///home/user/document.pdf`)

This design allows MCP clients to handle file selection and URI construction while the server focuses on the actual upload implementation.
