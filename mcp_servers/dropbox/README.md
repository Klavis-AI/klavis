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
- **Upload File**: Upload files with content as string or base64
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
- **Get Preview**: Get file previews for supported formats

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
Upload a file
```typescript
{
  path: string, // Upload path (e.g., "/folder/filename.txt")
  content: string, // File content as string or base64
  mode: "add" | "overwrite" | "update" (optional, default: "add"),
  autorename: boolean (optional, default: false),
  mute: boolean (optional, default: false)
}
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

### get_preview
Get file preview
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
