# Proof of Correctness Videos

This folder contains proof of correctness for all E2B MCP Server tools as required by the Klavis AI submission guidelines.

## Video Access

Due to large file sizes, all proof videos are hosted on Google Drive:

**🎥 Access Link**: https://drive.google.com/drive/folders/1jkqqiY7brz0OfGZT3MwDdJRfrzMqq9mc?usp=drive_link

## Video Contents

The following videos demonstrate each tool working with natural language queries in Claude Desktop/Cursor, showing server logs and successful results:

### Core Execution Tools
- `python_execute.mov` - Execute Python code in sandboxed environment
- `javascript_execute.mov` - Execute JavaScript/Node.js code
- `combined_workflow.mov` - Complete workflow demonstration

### File Management Tools  
- `write_file.mov` - Create files in sandbox (create_file tool)
- `read_file.mov` - Read files from sandbox
- `list_files.mov` - List directory contents

### Package Management
- `install_python_packages.mov` - Install Python packages via pip
- `js_packages_installation.mov` - Install JavaScript packages via npm

### System Information
- `sandbox_status.mov` - Get sandbox information and status
- `active_sandbox.mov` - Sandbox lifecycle management
- `available_tools.mov` - Tool discovery and listing

## What Each Video Shows

Each video demonstrates:
1. **Natural Language Query** - Human request in Claude Desktop/Cursor
2. **Tool Selection** - AI correctly identifying and calling the right MCP tool
3. **Server Logs** - E2B MCP server processing the request
4. **Successful Result** - Expected output returned to the AI client

This serves as undeniable proof of functionality and living documentation as required by the Klavis AI submission guidelines.

## Technical Details

- **Client**: Claude Desktop / Cursor IDE
- **Server**: E2B MCP Server (TypeScript)
- **Environment**: Sandboxed code execution via E2B API
- **Languages**: Python and JavaScript/Node.js
- **Security**: Input validation, output sanitization, resource limits

All tools have been tested end-to-end and work reliably with natural language instructions.