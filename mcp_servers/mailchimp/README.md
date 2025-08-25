# Mailchimp MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Mailchimp API](https://img.shields.io/badge/Mailchimp_API-v3.0-FFE01B.svg)](https://mailchimp.com/developer/marketing/api/)

## 📖 Overview

Mailchimp MCP Server is a Model Context Protocol (MCP) implementation that bridges language models and other applications with Mailchimp's Marketing API. It provides a standardized interface for executing email marketing operations through various tools defined by the MCP standard.

## 🚀 Features

This server provides comprehensive email marketing capabilities through MCP tools:

### Authentication & Account Management
| Tool | Description |
|------|-------------|
| `mailchimp_ping` | Test API connection and verify authentication |
| `mailchimp_get_account_info` | Get account details, subscription plan, and statistics |

### Audience Management
| Tool | Description |
|------|-------------|
| `mailchimp_get_all_audiences` | List all audiences with pagination and filtering |
| `mailchimp_create_audience` | Create new email lists with contact information |
| `mailchimp_get_audience_info` | Get detailed information about specific audiences |
| `mailchimp_update_audience` | Update audience settings and configuration |
| `mailchimp_delete_audience` | Permanently delete audiences (irreversible) |

### Member/Contact Management
| Tool | Description |
|------|-------------|
| `mailchimp_get_audience_members` | Retrieve members from audiences with filtering |
| `mailchimp_add_member_to_audience` | Add new contacts to audiences |
| `mailchimp_get_member_info` | Get detailed member information and activity |
| `mailchimp_update_member` | Update member details and subscription status |
| `mailchimp_delete_member` | Permanently remove members (irreversible) |
| `mailchimp_add_member_tags` | Add tags for member organization and segmentation |
| `mailchimp_remove_member_tags` | Remove tags from members |
| `mailchimp_get_member_activity` | Get member engagement history and activity |

### Campaign Management
| Tool | Description |
|------|-------------|
| `mailchimp_get_all_campaigns` | List campaigns with advanced filtering options |
| `mailchimp_create_campaign` | Create new email campaigns |
| `mailchimp_get_campaign_info` | Get campaign details and performance statistics |
| `mailchimp_set_campaign_content` | Set HTML content, templates, or plain text |
| `mailchimp_send_campaign` | Send campaigns immediately |
| `mailchimp_schedule_campaign` | Schedule campaigns for future delivery |
| `mailchimp_delete_campaign` | Delete draft campaigns (sent campaigns cannot be deleted) |

## 🔧 Prerequisites

You'll need one of the following:

- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.12+ with pip

## ⚙️ Setup & Configuration

### Mailchimp API Key Setup

1. **Log into your Mailchimp account**:
   - Navigate to your [Mailchimp Dashboard](https://mailchimp.com/)
   - Click on your profile icon in the top right corner
   - Select "Profile" from the dropdown menu

2. **Generate an API Key**:
   - In your profile, click on "Extras" dropdown
   - Select "API keys"
   - Click "Create A Key" button
   - Give your key a descriptive name (e.g., "MCP Server Integration")
   - Click "Generate Key"
   - **Important**: Copy the generated key immediately and store it securely
   - You won't be able to see the full key again after this step

3. **Find your Data Center**:
   - Your API key will be in the format: `key-datacenter` (e.g., `abc123def456-us6`)
   - The part after the dash (`us6` in this example) is your data center
   - You can also find this in your Mailchimp account URL

### Environment Configuration

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your Mailchimp credentials:
   ```
   MAILCHIMP_API_KEY=your_actual_mailchimp_api_key_here-us6
   MAILCHIMP_MCP_SERVER_PORT=5001
   ```

   **Important**: Replace `your_actual_mailchimp_api_key_here-us6` with your actual API key from step 2 above.

## 🏃‍♂️ Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t mailchimp-mcp-server -f mcp_servers/mailchimp/Dockerfile .

# Run the container
docker run -d -p 5001:5001 --name mailchimp-mcp mailchimp-mcp-server
```

To use your local .env file instead of building it into the image:

```bash
docker run -d -p 5001:5001 --env-file mcp_servers/mailchimp/.env --name mailchimp-mcp mailchimp-mcp-server
```

### Option 2: Python Virtual Environment

```bash
# Navigate to the Mailchimp server directory
cd mcp_servers/mailchimp

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Once running, the server will be accessible at `http://localhost:5001`.

## 🔌 API Usage

The server implements the Model Context Protocol (MCP) standard. Here's an example of how to call a tool:

```python
import httpx

async def call_mailchimp_tool():
    url = "http://localhost:5001/mcp"
    payload = {
        "tool_name": "mailchimp_get_all_audiences",
        "tool_args": {
            "count": 5,
            "offset": 0
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        result = response.json()
        return result
```

## 📋 Common Operations

### Testing Connection

```python
payload = {
    "tool_name": "mailchimp_ping",
    "tool_args": {}
}
```

### Getting Account Information

```python
payload = {
    "tool_name": "mailchimp_get_account_info",
    "tool_args": {}
}
```

### Creating an Audience

```python
payload = {
    "tool_name": "mailchimp_create_audience",
    "tool_args": {
        "name": "Newsletter Subscribers",
        "contact": {
            "company": "Your Company",
            "address1": "123 Main St",
            "city": "Your City",
            "state": "Your State",
            "zip": "12345",
            "country": "US"
        },
        "permission_reminder": "You subscribed to our newsletter on our website.",
        "from_name": "Your Company",
        "from_email": "newsletter@yourcompany.com",
        "subject": "Newsletter from Your Company",
        "language": "EN_US"
    }
}
```

### Adding a Member to an Audience

```python
payload = {
    "tool_name": "mailchimp_add_member_to_audience",
    "tool_args": {
        "list_id": "your_audience_id",
        "email_address": "john.doe@example.com",
        "status": "subscribed",
        "merge_fields": {
            "FNAME": "John",
            "LNAME": "Doe"
        },
        "tags": ["newsletter", "customer"]
    }
}
```

### Creating and Sending a Campaign

```python
# 1. Create campaign
create_payload = {
    "tool_name": "mailchimp_create_campaign",
    "tool_args": {
        "type": "regular",
        "list_id": "your_audience_id",
        "subject_line": "Welcome to our Newsletter!",
        "from_name": "Your Company",
        "reply_to": "support@yourcompany.com",
        "title": "Welcome Campaign"
    }
}

# 2. Set content
content_payload = {
    "tool_name": "mailchimp_set_campaign_content",
    "tool_args": {
        "campaign_id": "campaign_id_from_step_1",
        "html": "<h1>Welcome!</h1><p>Thanks for subscribing to our newsletter.</p>",
        "plain_text": "Welcome!\n\nThanks for subscribing to our newsletter."
    }
}

# 3. Send campaign
send_payload = {
    "tool_name": "mailchimp_send_campaign",
    "tool_args": {
        "campaign_id": "campaign_id_from_step_1"
    }
}
```

## 🛠️ Troubleshooting

### Docker Build Issues

- **File Not Found Errors**: If you see errors like `failed to compute cache key: failed to calculate checksum of ref: not found`, this means Docker can't find the files referenced in the Dockerfile. Make sure you're building from the root project directory (`klavis/`), not from the server directory.

### Common Runtime Issues

- **Authentication Failures**: 
  - Verify your API key is correct and includes the data center suffix (e.g., `-us6`)
  - Check that your API key hasn't been deleted or regenerated in Mailchimp
  - Ensure you're using the correct data center for your account

- **API Rate Limiting**: 
  - Mailchimp enforces rate limits based on your subscription plan
  - Free accounts have lower limits than paid accounts
  - Implement appropriate delays between requests if hitting limits

- **Permission Errors**: 
  - Some operations require specific Mailchimp subscription levels
  - Certain endpoints may require additional permissions or account verification
  - Check Mailchimp's API documentation for feature availability by plan

- **Invalid List/Campaign IDs**: 
  - Ensure you're using the correct IDs returned by the API
  - List IDs and Campaign IDs are unique identifiers, not names
  - Use `get_all_audiences` or `get_all_campaigns` to find valid IDs

- **Member Already Exists Errors**: 
  - Use `mailchimp_update_member` instead of `mailchimp_add_member_to_audience` for existing members
  - Mailchimp prevents duplicate email addresses in the same audience

### API Key Format Issues

Your API key should be in the format: `key-datacenter` (e.g., `abc123def456-us6`)

- If you get "Invalid API key" errors, verify the format is correct
- The data center part (after the dash) must match your account's data center
- You can find your data center in your Mailchimp account URL or API key

## 📊 API Limits and Best Practices

### Rate Limits
- **Free Plans**: 2,000 emails/month, limited API calls
- **Paid Plans**: Higher limits based on subscription level
- **Concurrent Requests**: Limit concurrent requests to avoid throttling

### Best Practices
- **Batch Operations**: Use batch endpoints when available for bulk operations
- **Error Handling**: Always implement proper error handling for API calls
- **Data Validation**: Validate email addresses and required fields before API calls
- **Pagination**: Use pagination for large result sets to avoid timeouts
- **Caching**: Cache frequently accessed data like audience lists to reduce API calls

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Links

- [Mailchimp Marketing API Documentation](https://mailchimp.com/developer/marketing/api/)
- [Model Context Protocol (MCP) Specification](https://github.com/modelcontextprotocol/specification)
- [Mailchimp Developer Portal](https://mailchimp.com/developer/)
- [Mailchimp API Quick Start Guide](https://mailchimp.com/developer/marketing/guides/quick-start/)