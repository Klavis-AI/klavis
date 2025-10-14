# Intercom MCP Server

This directory contains a Model Context Protocol (MCP) server for integrating [Intercom](https://www.intercom.com/) capabilities into applications like Claude, Cursor, and other LLM clients. It allows leveraging Intercom's powerful customer messaging and support platform features through a standardized protocol.

## Features

This server exposes **69 comprehensive tools** covering the full Intercom API functionality:

### Contact Management (12 tools)

- `intercom_list_contacts`: Get all contacts with pagination and filtering support
- `intercom_get_contact`: Retrieve detailed information about specific contacts
- `intercom_create_contact`: Create new contacts with flexible requirements (email, external_id, or role)
- `intercom_update_contact`: Update existing contact properties and custom attributes
- `intercom_delete_contact`: Permanently remove contacts from workspace
- `intercom_search_contacts`: Advanced contact search with complex query filters and operators
- `intercom_merge_contact`: Merge lead contacts into user contacts
- `intercom_list_contact_notes`: Get all notes attached to a specific contact
- `intercom_create_contact_note`: Add internal notes to contact records
- `intercom_list_contact_tags`: List all tags associated with a contact
- `intercom_add_contact_tag`: Tag contacts for organization and segmentation
- `intercom_remove_contact_tag`: Remove tags from contacts

### Conversation Management (12 tools)

- `intercom_list_conversations`: Get all conversations with pagination and display options
- `intercom_get_conversation`: Retrieve complete conversation details with all message parts
- `intercom_create_conversation`: Create conversations initiated by contacts
- `intercom_update_conversation`: Update conversation properties (read status, title, custom attributes)
- `intercom_delete_conversation`: Remove conversations from workspace
- `intercom_search_conversations`: Advanced conversation search with filtering and operators
- `intercom_reply_conversation`: Reply to conversations (admin/user replies, notes, quick replies)
- `intercom_manage_conversation`: Manage conversation state (close, snooze, open, assign)
- `intercom_attach_contact_to_conversation`: Add participants to group conversations
- `intercom_detach_contact_from_conversation`: Remove participants from conversations
- `intercom_redact_conversation`: Redact conversation parts or source messages
- `intercom_convert_conversation_to_ticket`: Convert conversations to support tickets

### Company Management (13 tools)

- `intercom_list_companies`: Get all companies with pagination and ordering
- `intercom_get_company`: Retrieve detailed company information
- `intercom_create_company`: Create new companies with business data and custom attributes
- `intercom_update_company`: Update company properties, metrics, and custom data
- `intercom_delete_company`: Remove companies from workspace
- `intercom_find_company`: Find companies using external company IDs
- `intercom_list_company_users`: Get all users belonging to a specific company
- `intercom_attach_contact_to_company`: Associate contacts with companies
- `intercom_detach_contact_from_company`: Remove contact-company associations
- `intercom_list_company_segments`: Get segments that a company belongs to
- `intercom_list_company_tags`: List tags attached to companies
- `intercom_tag_company`: Tag companies (supports bulk operations)
- `intercom_untag_company`: Remove tags from companies (supports bulk operations)

### Help Center & Knowledge Base (11 tools)

- `intercom_list_articles`: Get all Help Center articles with pagination
- `intercom_get_article`: Retrieve specific article content and metadata
- `intercom_create_article`: Create new Help Center articles with multilingual support
- `intercom_update_article`: Update article content, state, and translations
- `intercom_delete_article`: Remove articles from Help Center
- `intercom_search_articles`: Search articles by phrase, state, author, and parent
- `intercom_list_collections`: Get all Help Center collections
- `intercom_get_collection`: Retrieve collection details and structure
- `intercom_create_collection`: Create new collections with hierarchy support
- `intercom_update_collection`: Update collection properties and translations
- `intercom_delete_collection`: Remove collections from Help Center

### Messaging & Communication (7 tools)

- `intercom_create_message`: Send admin-initiated messages (in-app or email)
- `intercom_list_messages`: Get all messages sent from workspace
- `intercom_get_message`: Retrieve specific message details
- `intercom_create_note`: Add internal notes to contact records
- `intercom_list_notes`: Get notes for specific contacts with pagination
- `intercom_get_note`: Retrieve specific note details
- `intercom_send_user_message`: Create user/contact-initiated conversations

### Tags & Segmentation (7 tools)

- `intercom_list_tags`: Get all workspace tags
- `intercom_get_tag`: Retrieve specific tag information
- `intercom_create_or_update_tag`: Create new tags or update existing ones
- `intercom_tag_companies`: Tag companies (supports bulk operations)
- `intercom_untag_companies`: Remove tags from companies (supports bulk operations)
- `intercom_tag_users`: Tag multiple users/contacts at once
- `intercom_delete_tag`: Remove tags from workspace

### Team & Admin Management (7 tools)

- `intercom_list_teams`: Get all teams in workspace
- `intercom_get_team`: Retrieve team details with admin members
- `intercom_list_admins`: Get all admin users/teammates
- `intercom_get_admin`: Retrieve specific admin details
- `intercom_get_current_admin`: Get currently authenticated admin information
- `intercom_set_admin_away`: Set admin away status with conversation reassignment
- `intercom_list_admin_activity_logs`: Get audit trail of admin activities

## Prerequisites

- **Node.js:** Version 18.0.0 or higher
- **npm:** Node Package Manager (usually comes with Node.js)
- **TypeScript:** For development and building
- **Intercom Access Token:** Obtainable from your [Intercom Developer Hub](https://developers.intercom.com/)

## Environment Setup

Before running the server, you need to configure your Intercom API credentials.

1. Create an environment file:
cp .env.example .env


**Note:** If `.env.example` doesn't exist, create `.env` directly:

touch .env

2. Edit `.env` and add your Intercom access token:

Intercom API credentials
INTERCOM_ACCESS_TOKEN=your-actual-access-token-here
PORT=5000


- `INTERCOM_ACCESS_TOKEN` (Required): Your access token for the Intercom API. You can obtain this from your Intercom Developer Hub by creating an app and generating an access token.
- `PORT` (Optional): The port number for the server to listen on. Defaults to 5000.

## Getting Your Intercom Access Token

### For Development (Access Token):

1. Visit the [Intercom Developer Hub](https://developers.intercom.com/)
2. Sign in with your Intercom account
3. Create a new app or select an existing one
4. Go to the "Authentication" tab
5. Copy the Access Token (typically starts with `dG9r:`)
6. Use this token as your `INTERCOM_ACCESS_TOKEN`

### Required Scopes:

Ensure your Intercom app has the necessary scopes for the APIs you want to use:
- `read:contacts` - For contact management tools
- `write:contacts` - For creating/updating contacts
- `read:conversations` - For conversation management tools
- `write:conversations` - For creating/updating conversations
- `read:companies` - For company management tools
- `write:companies` - For creating/updating companies
- `read:articles` - For Help Center tools
- `write:articles` - For creating/updating articles
- `read:admins` - For team management tools

## Running Locally

### Using Node.js / npm

1. **Install Dependencies:**
npm install



2. **Build the Server Code:**

npm run build

3. **Start the Server:**

npm start


The server will start using the environment variables defined in `.env` and listen on port 5000 (or the port specified by the `PORT` environment variable).

## API Reference

### Key Tool Examples

#### Contact Management

##### `intercom_create_contact`

Create a new contact in your Intercom workspace.

**Parameters:**

- `role` (string, optional): "user" or "lead"
- `external_id` (string, optional): Your unique identifier for the contact
- `email` (string, optional): Contact's email address
- `phone` (string, optional): Contact's phone number
- `name` (string, optional): Contact's name
- `signed_up_at` (number, optional): UNIX timestamp of signup
- `custom_attributes` (object, optional): Custom data for the contact

**Note:** At least one of `email`, `external_id`, or `role` must be provided.

##### `intercom_search_contacts`

Search contacts using advanced query filters.

**Parameters:**

- `query` (object, required): Search query with field, operator, and value
- `pagination` (object, optional): Pagination options with per_page and starting_after

**Example query:**
{
"query": {
"field": "email",
"operator": "=",
"value": "user@example.com"
}
}


#### Conversation Management

##### `intercom_create_conversation`

Create a conversation initiated by a contact.

**Parameters:**

- `from` (object, required): Contact object with type and id
- `body` (string, required): Message content
- `created_at` (number, optional): UNIX timestamp

##### `intercom_reply_conversation`

Reply to an existing conversation.

**Parameters:**

- `id` (string, required): Conversation ID
- `message_type` (string, optional): "comment", "note", or "quick_reply"
- `type` (string, optional): "admin" or "user"
- `admin_id` (string, optional): ID of replying admin
- `body` (string, optional): Reply content

#### Company Management

##### `intercom_create_company`

Create a new company in your workspace.

**Parameters:**

- `name` (string, optional): Company name
- `company_id` (string, optional): Your unique identifier
- `plan` (string, optional): Company's plan/tier
- `size` (number, optional): Number of employees
- `website` (string, optional): Company website URL
- `monthly_spend` (number, optional): Revenue from this company
- `custom_attributes` (object, optional): Custom company data

**Note:** At least one of `name` or `company_id` must be provided.

#### Help Center Management

##### `intercom_create_article`

Create a new Help Center article.

**Parameters:**

- `title` (string, required): Article title
- `author_id` (number, required): ID of the author (must be a teammate)
- `description` (string, optional): Article description
- `body` (string, optional): Article content (HTML supported)
- `state` (string, optional): "published" or "draft"
- `translated_content` (object, optional): Multilingual content

#### Messaging

##### `intercom_create_message`

Send an admin-initiated message.

**Parameters:**

- `message_type` (string, required): "in_app" or "email"
- `body` (string, required): Message content
- `from` (object, required): Admin sender object
- `to` (object, required): Contact recipient object
- `subject` (string, required for email): Email subject line
- `template` (string, required for email): "plain" or "personal"

## Authentication

The server supports two methods of authentication:

1. **Environment Variable (Recommended):** Set `INTERCOM_ACCESS_TOKEN` in your `.env` file.
2. **HTTP Header:** Pass the access token as `x-auth-token` header in requests to the MCP server.

Both Bearer token format (`Bearer dG9r:token123`) and direct token format (`dG9r:token123`) are supported.

## Protocol Support

This server supports both MCP protocol versions:

- **Streamable HTTP Transport** (Protocol Version 2025-03-26) - **Recommended**
  - Endpoint: `POST /mcp`
  - Single request/response model
  - Simpler implementation and better performance

- **HTTP+SSE Transport** (Protocol Version 2024-11-05) - **Legacy Support**
  - Endpoints: `GET /sse`, `POST /messages`, `DELETE /sse/:sessionId`
  - Persistent connections with session management
  - Server-Sent Events for real-time communication

### Additional Endpoints

- `GET /health` - Health check endpoint
- `GET /sse/status` - SSE connection status and monitoring

## Testing with MCP Clients

### Claude Desktop

Add to your MCP configuration:

{
"mcpServers": {
"intercom": {
"command": "node",
"args": ["path/to/your/server/dist/index.js"],
"env": {
"INTERCOM_ACCESS_TOKEN": "your_actual_token_here"
}
}
}
}

text

### Cursor IDE

1. Create `.cursor/mcp.json` in your project:
{
"mcpServers": {
"intercom": {
"url": "http://localhost:5000/mcp",
"headers": {
"x-auth-token": "your_actual_token_here"
}
}
}
}

text

2. Test with natural language:
- "Create a new contact with email john@example.com"
- "List all conversations from the last week"
- "Search for companies with more than 100 employees"
- "Create a Help Center article about getting started"
- "Tag all enterprise customers with 'high-value'"

## Error Handling

The server includes comprehensive error handling:

- **Authentication errors**: Invalid or missing tokens, insufficient permissions
- **API errors**: Intercom API rate limits, invalid parameters, resource not found
- **Connection errors**: Network issues and timeouts
- **Validation errors**: Invalid input parameters, missing required fields

All errors are returned in proper JSON-RPC format with descriptive error messages and appropriate HTTP status codes.

## Rate Limiting

The server respects Intercom's API rate limits:
- **Standard rate limit**: 1000 requests per minute
- **Search endpoints**: 333 requests per minute
- **Bulk operations**: Automatic batching to optimize request usage

## Development

- **Building:** `npm run build` (compile TypeScript to JavaScript)
- **Development:** `npm run dev` (build and run with file watching)
- **Linting:** `npm run lint` (check code style)
- **Format:** `npm run format` (format code with Prettier)
- **Testing:** `npm test` (run test suite)

## Architecture

The server is built with:

- **Express.js** for HTTP server functionality
- **Model Context Protocol SDK** for MCP implementation
- **AsyncLocalStorage** for request context management
- **TypeScript** for type safety and better development experience
- **Comprehensive validation** for all input parameters
- **Modular handler architecture** for maintainable code organization

## Project Structure

src/
├── client/ # Intercom API client
│ └── intercomClient.ts
├── tools/ # MCP tool definitions and handlers
│ ├── definitions/ # Tool schema definitions
│ │ ├── contactTools.ts
│ │ ├── conversationTools.ts
│ │ ├── companyTools.ts
│ │ ├── articleTools.ts
│ │ ├── messageTools.ts
│ │ ├── tagTools.ts
│ │ ├── teamTools.ts
│ │ └── index.ts
│ ├── handlers/ # Tool implementation logic
│ │ ├── contactHandler.ts
│ │ ├── conversationHandler.ts
│ │ ├── companyHandler.ts
│ │ ├── articleHandler.ts
│ │ ├── messageHandler.ts
│ │ ├── tagHandler.ts
│ │ ├── teamHandler.ts
│ │ └── index.ts
│ └── index.ts
├── transport/ # MCP transport implementations
│ ├── httpTransport.ts
│ └── sseTransport.ts
├── utils/ # Utility functions
│ ├── validation.ts
│ └── errors.ts
├── server.ts # MCP server configuration
└── index.ts # Main application entry point

text

## Support

For issues related to this MCP server, please create an issue in the repository.
For Intercom API questions, consult the [Intercom API documentation](https://developers.intercom.com/reference/).
