
# Klaviyo MCP Server
A Python server for interacting with the Klaviyo API using MCP tools.

## Features

- Create and retrieve Klaviyo profiles
- Manage lists and campaigns
- Fetch and render templates
- Access account and flow information
- Built-in retry, pagination, and error handling

## Available MCP Tools

### Profile Tools

- **get_profile**: Retrieve details for a specific Klaviyo profile using an email address or other identifier.
- **create_or_update_profile_single**: Create a new profile or update an existing one with provided details (such as email).

### List Tools

- **get_lists**: Fetch all available mailing lists in the connected Klaviyo account.
- **get_list**: Retrieve details for a specific mailing list.
- **get_profiles_for_list**: List all profiles (subscribers) associated with a specific mailing list.
- **create_list**: Create a new mailing list in Klaviyo.

### Metrics Tools

- **get_metrics**: Retrieve standard metrics tracked in the Klaviyo account (such as email opens, clicks, etc.).
- **get_custom_metrics**: Fetch custom metrics that have been defined in the Klaviyo account.

### Template Tools

- **get_templates**: List all available email templates in the Klaviyo account.
- **render_template**: Render a specific template, possibly with dynamic data.

### Campaign Tools

- **create_campaign**: Create a new email campaign in Klaviyo.
- **get_campaigns**: List all campaigns in the account.
- **get_campaign**: Retrieve details for a specific campaign by its ID.

### Account Tools

- **get_account_details**: Fetch account-level details and settings from Klaviyo.
- **list_accounts**: List all accounts accessible via the current credentials (if applicable).

### Flows and Forms Tools

- **get_flows**: Retrieve all flows (automated sequences) configured in the Klaviyo account.

## Project Setup Instructions

## Requirements

- Python 3.10+
- See [requirements.txt](requirements.txt) for dependencies

### IDEs to Install

- **Client:** Claude Desktop  
- **MCP Server:** Visual Studio Code (VSC)


### Installation Steps

1. Install the `uv` package:
   ```bash
   pip3 install uv
   ```
2. Clone the repository and navigate to the `mcp_servers/klaviyo` directory.
3. Install dependencies:
   ```bash
    pip install -r requirements.txt
   ```
4. Copy the example environment file and update credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your Klaviyo API credentials
   ```
5. Start the MCP server:
   ```bash
   uv run mcp install main.py
   ```

### Additional Notes

- Ensure Python 3.10+ is installed.
- For development, use a virtual environment or `uv` for dependency management.
- For any issues, please refer to the main project documentation or open an issue.