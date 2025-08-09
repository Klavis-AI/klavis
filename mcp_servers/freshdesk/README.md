# Freshdesk MCP Server

A comprehensive Model Context Protocol (MCP) server for Freshdesk that enables AI agents to manage customer support operations programmatically. This server provides full access to Freshdesk's API capabilities through a standardized MCP interface.

## Overview

The MCP supports both SSE (Server-Sent Events) and StreamableHTTP transports for flexible integration with various AI platforms.

## Features

### 🎫 Ticket Management
- **Create, Read, Update, Delete** tickets with full metadata support
- **Add notes and replies** to tickets with HTML content
- **Forward tickets** to additional email addresses
- **Merge multiple tickets** for better organization
- **Watch/unwatch tickets** for real-time updates
- **Restore deleted tickets** from archive
- **Advanced filtering and search** with multiple criteria
- **Attachment handling** for file uploads and management
- **Archive management** for deleted ticket operations

### 👥 Contact Management
- **Create and manage** customer contacts with detailed profiles
- **Search contacts** by name with autocomplete functionality
- **Filter contacts** by various criteria (email, phone, company, etc.)
- **Convert contacts to agents** with role assignments
- **Merge multiple contacts** into primary contacts
- **Restore deleted contacts** from soft delete
- **Send contact invitations** for portal access

### 🏢 Company Management
- **Create and manage** companies with organizational data
- **Search companies** by name with autocomplete
- **Filter companies** using flexible query strings
- **Update company information** and custom fields

### 👨‍💼 Agent Management
- **List and manage** support agents with detailed profiles
- **Create new agents** with specific roles and permissions
- **Update agent information** including skills and groups
- **Search agents** by name or email
- **Bulk create agents** for efficient onboarding
- **Delete agents** (downgrades to contact)
- **Get authenticated agent** details

### 💬 Thread Management
- **Create different thread types**: forward, discussion, private
- **Manage thread messages** with HTML and plain text support
- **Handle participants** (emails and agents)
- **Email configuration** for thread forwarding
- **Update and delete** threads and messages

### 🔧 Account Management
- **Retrieve current account** information

## Quick Start

### Prerequisites

- Python 3.8+
- Freshdesk account with API access
- Freshdesk API key and domain

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mcp_servers/freshdesk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export FRESHDESK_API_KEY="your_api_key_here"
   export FRESHDESK_DOMAIN="your_domain"
   export FRESHDESK_MCP_SERVER_PORT="5000"  # Optional, default is 5000
   ```

4. **Run the server**
   ```bash
   python server.py
   ```

### Docker Deployment

```bash
# Build the image
docker build -t freshdesk-mcp-server .

# Run the container
docker run -p 5000:5000 \
  -e FRESHDESK_API_KEY="your_api_key" \
  -e FRESHDESK_DOMAIN="your_domain" \
  freshdesk-mcp-server
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FRESHDESK_API_KEY` | Your Freshdesk API key | Yes | - |
| `FRESHDESK_DOMAIN` | Your Freshdesk domain | Yes | - |
| `FRESHDESK_MCP_SERVER_PORT` | Server port | No | 5000 |


### Freshdesk Domain

The Freshdesk domain is the unique identifier for your Freshdesk account. It is used to make API requests to the Freshdesk API. The domain is typically in the format `your_domain.freshdesk.com`. You can read more here: [Freshdesk API Documentation](https://developers.freshdesk.com/api/#getting-started):

<img width="912" height="567" alt="Screenshot 2025-08-08 at 18 31 56" src="https://github.com/user-attachments/assets/4bbb2d3f-1243-4a01-99af-69482b1c7cb5" />

You can find your Freshdesk domain in the Freshdesk settings:

<img width="427" height="289" alt="Screenshot 2025-08-08 at 18 29 17" src="https://github.com/user-attachments/assets/f3c12afb-aaad-4104-8eeb-668347e6d1ab" />


### Server Options

```bash
python server.py --help
```

Available options:
- `--port`: Port to listen on (default: 5000)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--json-response`: Enable JSON responses for StreamableHTTP

## API Reference

### Transport Endpoints

- **SSE Endpoint**: `http://localhost:5000/sse`
- **StreamableHTTP Endpoint**: `http://localhost:5000/mcp`

### Tool Categories

#### Ticket Tools

| Tool | Description | Required Parameters |
|------|-------------|-------------------|
| `freshdesk_create_ticket` | Create a new ticket | `subject`, `description`, `email` |
| `freshdesk_get_ticket_by_id` | Retrieve a ticket | `ticket_id` |
| `freshdesk_update_ticket` | Update ticket details | `ticket_id` |
| `freshdesk_delete_ticket` | Delete a ticket | `ticket_id` |
| `freshdesk_add_note_to_ticket` | Add a note to ticket | `ticket_id`, `body` |
| `freshdesk_reply_to_a_ticket` | Reply to a ticket | `ticket_id`, `body` |
| `freshdesk_forward_ticket` | Forward ticket to emails | `ticket_id`, `to_emails` |
| `freshdesk_merge_tickets` | Merge multiple tickets | `primary_ticket_id`, `ticket_ids` |
| `freshdesk_list_tickets` | List tickets with filtering | - |
| `freshdesk_filter_tickets` | Filter tickets by criteria | `query` |

#### Contact Tools

| Tool | Description | Required Parameters |
|------|-------------|-------------------|
| `freshdesk_create_contact` | Create a new contact | `name` |
| `freshdesk_get_contact_by_id` | Retrieve a contact | `contact_id` |
| `freshdesk_update_contact` | Update contact details | `contact_id` |
| `freshdesk_delete_contact` | Delete a contact | `contact_id` |
| `freshdesk_search_contacts_by_name` | Search contacts by name | `name` |
| `freshdesk_filter_contacts` | Filter contacts | - |
| `freshdesk_make_contact_agent` | Convert contact to agent | `contact_id` |
| `freshdesk_merge_contacts` | Merge multiple contacts | `primary_contact_id`, `contact_ids` |

#### Company Tools

| Tool | Description | Required Parameters |
|------|-------------|-------------------|
| `freshdesk_create_company` | Create a new company | `name` |
| `freshdesk_get_company_by_id` | Retrieve a company | `company_id` |
| `freshdesk_update_company` | Update company details | `company_id` |
| `freshdesk_delete_company` | Delete a company | `company_id` |
| `freshdesk_search_companies_by_name` | Search companies by name | `name` |
| `freshdesk_filter_companies` | Filter companies | `query` |

#### Agent Tools

| Tool | Description | Required Parameters |
|------|-------------|-------------------|
| `freshdesk_list_agents` | List all agents | - |
| `freshdesk_get_agent_by_id` | Get agent details | `agent_id` |
| `freshdesk_create_agent` | Create a new agent | `email`, `name`, `ticket_scope`, `role_ids` |
| `freshdesk_update_agent` | Update agent details | `agent_id` |
| `freshdesk_delete_agent` | Delete an agent | `agent_id` |
| `freshdesk_search_agents` | Search agents | `query` |
| `freshdesk_bulk_create_agents` | Create multiple agents | `agents_data` |
| `freshdesk_get_current_agent` | Get current agent details | - |


#### Thread Tools

| Tool | Description | Required Parameters |
|------|-------------|-------------------|
| `freshdesk_create_thread` | Create a new thread | `thread_type`, `parent_id` |
| `freshdesk_get_thread_by_id` | Get thread details | `thread_id` |
| `freshdesk_update_thread` | Update thread details | `thread_id` |
| `freshdesk_delete_thread` | Delete a thread | `thread_id` |
| `freshdesk_create_thread_message` | Add message to thread | `thread_id`, `body` |
| `freshdesk_get_thread_message_by_id` | Get message details | `message_id` |
| `freshdesk_update_thread_message` | Update message | `message_id` |
| `freshdesk_delete_thread_message` | Delete message | `message_id` |

#### Account Tools

| Tool | Description | Required Parameters |
|------|-------------|-------------------|
| `freshdesk_get_current_account` | Get account details | - |

## Usage Examples

### Creating a Ticket

```json
{
  "name": "freshdesk_create_ticket",
  "arguments": {
    "subject": "Technical Support Request",
    "description": "<p>I'm experiencing issues with the login system.</p>",
    "email": "customer@example.com",
    "name": "John Doe",
    "priority": 2,
    "status": 2,
    "tags": ["technical", "login"]
  }
}
```

### Adding a Note to a Ticket

```json
{
  "name": "freshdesk_add_note_to_ticket",
  "arguments": {
    "ticket_id": 12345,
    "body": "Investigating the login issue. Will update shortly.",
    "private": false
  }
}
```

### Creating a Contact

```json
{
  "name": "freshdesk_create_contact",
  "arguments": {
    "name": "Jane Smith",
    "email": "jane.smith@company.com",
    "phone": "+1-555-0123",
    "company_id": 789,
    "description": "VIP customer"
  }
}
```

### Creating a Thread

```json
{
  "name": "freshdesk_create_thread",
  "arguments": {
    "thread_type": "private",
    "parent_id": 12345,
    "title": "Internal Discussion",
    "participants_agents": ["agent1", "agent2"]
  }
}
```

## Error Handling

The server provides comprehensive error handling:

- **API Errors**: Properly formatted error responses with details
- **Validation Errors**: Input validation with helpful error messages
- **Network Errors**: Automatic retry mechanisms for transient failures
- **Rate Limiting**: Built-in rate limiting to respect Freshdesk API limits

### Error Response Format

```json
{
  "message": "Error message",
  "details": [],
  "code": "not_found"
}
```

Enable debug logging for detailed troubleshooting:

```bash
python server.py --log-level DEBUG
```