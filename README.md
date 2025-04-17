<div align="center">
  <picture>
    <img src="https://raw.githubusercontent.com/klavis-ai/klavis/main/static/klavis-ai.png" width="80">
  </picture>
</div>

<h1 align="center">Making MCPs Accessible for Everyone 🚀</h1>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Website](https://img.shields.io/badge/Website-🌐-purple)](https://www.klavis.ai)
[![Discord](https://img.shields.io/discord/1356754991989133462?color=7289DA&label=Community&logo=discord&logoColor=white)](https://discord.com/invite/P6fFgv2w)
[![YouTube Demo](https://img.shields.io/badge/Demo-YouTube-red)](https://www.youtube.com/@KlavisAI-w2l)

## 📚 TL;DR

Klavis AI is building open-source infrastructure to make Model Context Protocols (MCPs) easy for everyone. We provide:

- 💬 **Slack & Discord Clients**: Run MCPs directly from your favorite messaging platforms
- ☁️ **Hosted MCP Servers**: Access powerful tools without infrastructure management
- 🎛️ **Simple Web UI**: Configure and manage everything with no coding required

Whether you're a non-technical user wanting to leverage AI workflows or a developer looking to build and scale MCPs, Klavis makes it simple.

## 🎬 Watch Our Demo

See how easy it is to use MCPs (like our Report Generator, YouTube tools, and Document Converters) directly from Slack/Discord:

[![Klavis AI Demo](https://i3.ytimg.com/vi/9-QQAhrQWw8/maxresdefault.jpg)](https://www.youtube.com/watch?v=9-QQAhrQWw8)

You can find more case study videos on [our website](https://www.klavis.ai). 

## 🚀 Quick Start

For detailed MCP client setup instructions, please refer to the platform-specific documentation:
- [**Discord Bot Setup Guide**](mcp_clients/README-Discord.md) - Complete instructions for setting up and running the Discord bot
- [**Slack Bot Setup Guide**](mcp_clients/README-Slack.md) - Step-by-step guide for creating a Slack app and connecting it

For detailed MCP server setup instructions, please refer to the README file under each server folder.

- [**Discord**](mcp_servers/discord/README.md): For Discord API integration
- [**Document Conversion (Pandoc)**](mcp_servers/pandoc/README.md): Convert between various file formats using Pandoc
- [**Firecrawl**](mcp_servers/firecrawl/README.md): For web crawling and data collection
- [**Firecrawl Deep Research**](mcp_servers/firecrawl_deep_research/README.md): For deeper web research tasks
- [**GitHub**](mcp_servers/github/README.md): Perform GitHub repository operations
- [**Markitdown**](mcp_servers/markitdown/README.md): Markdown conversion tool
- [**Postgres**](mcp_servers/postgres/README.md): For PostgreSQL database operations
- [**Report Generation**](mcp_servers/report_generation/README.md): Create professional web reports from user query
- [**Resend**](mcp_servers/resend/README.md): For email services
- [**Slack**](mcp_servers/slack/README.md): For Slack API integration
- [**Supabase**](mcp_servers/supabase/README.md): For database operations
- [**YouTube**](mcp_servers/youtube/README.md): Extract and convert YouTube video information

## 🏗️ Architecture

Klavis consists of two main components:

### MCP Servers

Located in the `mcp_servers/` directory, these service-specific modules expose capabilities as tools:

- **Report Generation**: Create professional reports from various data sources
- **YouTube**: Download, analyze, and transform YouTube content
- **Document Conversion**: Convert between various file formats using Pandoc
- **GitHub**: Perform GitHub repository operations
- **Slack**: For Slack API integration
- **Supabase**: For database operations
- **Firecrawl**: For web crawling and data collection
- **Resend**: For email services
- **Postgres**: For PostgreSQL database operations
- **Discord**: For Discord API integration

### MCP Clients

Located in the `mcp_clients/` directory, these client applications connect to MCP servers and interface with end-user platforms:

- **Discord Bot**: Interactive AI assistant for Discord
- **Slack Bot**: Interactive AI assistant for Slack
- **Base Client**: Shared functionality for all platform clients

## 🧩 Extending Klavis

### Adding a New Tool

1. Create a new directory in `mcp_servers/`
2. Implement the MCP server interface
3. Register your tools with appropriate schemas
4. Connect to your client through the standard SSE protocol

### Adding a New Client Platform

1. Create a new client module in `mcp_clients/`
2. Extend the `base_bot.py` functionality
3. Implement platform-specific message handling
4. Connect to MCP servers using `mcp_client.py`

## 🤝 Contributing

We love contributions! Join our [Discord community](https://discord.gg/cVNXvzs5) to discuss ideas and get help.

## 📚 Citation

If you use Klavis in your research or project, please cite:

```bibtex
@software{klavis2024,
  author = {Klavis AI},
  title = {Klavis: Open-Source Infrastructure for Model Context Protocols},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/klavis-ai/klavis}
}
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">
🙏 Thanks for checking out Klavis AI! We're excited to hear your thoughts and build this with the community.
</div> 