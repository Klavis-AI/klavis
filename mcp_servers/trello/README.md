# Trello MCP Server

A Model Context Protocol (MCP) server for Trello integration. Manage boards, lists, cards, and checklists using Trello's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🐳 Using Docker (For Self-Hosting)

```bash
# Build the Docker image
docker build -t trello-mcp-server .

# Run the server with your credentials
docker run -p 5002:5002 -e TRELLO_API_KEY="your_key" -e TRELLO_API_TOKEN="your_token" trello-mcp-server
```

### 💻 Local Development

```bash
# Navigate to the server directory
cd mcp_servers/trello

# Create and activate virtual environment
uv venv
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Create a .env file with your Trello credentials
# TRELLO_API_KEY=your_key
# TRELLO_API_TOKEN=your_token

# Run the server
python server.py
```

## 🛠️ Available Tools

### Board Operations
- `trello_get_my_boards`: Fetches all boards that the user is a member of.
- `trello_create_board`: Creates a new board.

### List Operations
- `trello_get_board_lists`: Fetches all lists in a specific board.

### Card Operations
- `trello_get_list_cards`: Fetches all cards in a specific list.
- `trello_create_card`: Creates a new card in a specific list.
- `trello_update_card`: Updates an existing card.
- `trello_delete_card`: Deletes a card.

### Checklist Operations
- `trello_create_checklist`: Creates a new checklist on a specific card.
- `trello_add_item_to_checklist`: Adds an item to a checklist.
- `trello_update_checklist_item_state`: Updates an item's state in a checklist (e.g., to 'complete').

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | [docs.klavis.ai](https://docs.klavis.ai) |
| **💬 Discord** | [Join Community](https://discord.gg/p7TuTEcssn) |
| **🐛 Issues** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📜 License

Apache 2.0 license - see [LICENSE](../../LICENSE) for details.
