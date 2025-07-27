# Dropbox MCP Server

A Model Context Protocol (MCP) server for Dropbox integration, providing comprehensive file management capabilities.

## Features

### File & Folder Operations
- **List Folder**: Lists the contents of a folder
- **Continue Folder Listing**: Continues listing folder contents using a cursor
- **Create Folder**: Creates a new folder
- **Delete File/Folder**: Deletes a file or folder
- **Move File/Folder**: Moves or renames a file or folder
- **Copy File/Folder**: Creates a copy of a file or folder

### Batch Operations
- **Batch Delete Files**: Deletes multiple files and folders in a single operation
- **Batch Move Files**: Moves or renames multiple files and folders in a single operation
- **Batch Copy Files**: Copies multiple files and folders in a single operation
- **Check Batch Job Status**: Checks the status of a batch operation

### File Content Operations
- **Upload File**: Uploads a local file to Dropbox using file:// URI
- **Download File**: Downloads a file from Dropbox
- **Get File Info**: Gets metadata information about a file or folder

### File Version Management
- **List Revisions**: Lists the revisions of a file
- **Restore File**: Restores a file to a previous revision

### Search & Discovery
- **Search Files**: Searches for files and folders
- **Continue File Search**: Continues searching files using a cursor
- **Get Shared Links**: Lists shared links for files and folders
- **Share File**: Creates a shared link for a file or folder

### Advanced Sharing & Collaboration
- **Add File Member**: Adds a member to a file
- **List File Members**: Lists the members of a file
- **Remove File Member**: Removes a member from a file
- **Share Folder**: Shares a folder
- **List Folder Members**: Lists the members of a shared folder
- **Add Folder Member**: Adds a member to a shared folder
- **Unshare File**: Removes all members from a file
- **Unshare Folder**: Allows a shared folder owner to unshare the folder
- **Remove Folder Member**: Removes a member from a shared folder

### File Requests
- **Create File Request**: Creates a file request
- **Get File Request**: Gets a file request by ID
- **List File Requests**: Lists all file requests
- **Delete File Request**: Deletes file requests
- **Update File Request**: Updates a file request

### Account Utilities
- **Get Current Account**: Gets information about the current account
- **Get Space Usage**: Gets the current space usage information

### Utilities
- **Get Temporary Link**: Gets a temporary link to a file
- **Get File Thumbnail**: Gets a thumbnail image for a file
- **Save URL to Dropbox**: Downloads content from a URL and saves it as a file in Dropbox
- **Check URL Save Status**: Checks the status of a save URL operation
- **Lock Files (Batch)**: Temporarily locks files to prevent them from being edited by others
- **Unlock Files (Batch)**: Unlocks previously locked files
- **List Received Files**: Lists files that have been shared with the current user by others
- **Check Job Status**: Checks the status of an asynchronous operation

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

> **Note**: These permissions are required for the server to provide full functionality. Some features may not work if certain permissions are not granted.

## Available Tools

For a comprehensive list of available tools, please refer to the [tools.ts](./src/tools.ts) file.

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and configure your Dropbox credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Dropbox app credentials:

```bash
# Server Port Configuration
PORT=5000

# Dropbox access token, get it from your Dropbox App settings
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
			"type": "http",
			"url": "http://localhost:5000/mcp",
			"headers": {
				"x-auth-token": "YOUR_DROPBOX_ACCESS_TOKEN"
			}
		}
  }
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

#### 2. Generate an Access Token

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

#### 3. Set Permissions

In your app settings, under "Permissions", ensure you have the necessary scopes enabled:
- `account_info.read` - For account information
- `files.metadata.write` - For file operations
- `files.content.write` - For uploading/downloading files
- `sharing.write` - For sharing operations
- `file_requests.write` - For sharing operations

### Environment Configuration

Create a `.env` file in the server directory:

```bash
# Optional: Server Configuration
PORT=5000
# Optional: Dropbox access token
DROPBOX_ACCESS_TOKEN=your_access_token_here
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

## Troubleshooting

### Common Issues

#### 401 Authentication Error
If you get a "Response failed with a 401 code" error:

1. **Check Token Expiration**: Access tokens generated via the Developer Console have a limited lifespan (typically 4 hours)
2. **Regenerate Token**: Go to your [Dropbox Developer Console](https://www.dropbox.com/developers/apps), find your app, and generate a new access token
3. **Update .env File**: Replace the `DROPBOX_ACCESS_TOKEN` value in your `.env` file
4. **Restart Server**: After updating the token, restart the server

#### Permission Errors
- Check that your app has the necessary scopes enabled in the Developer Console
- Ensure your account has the required permissions for the operations you're trying to perform
