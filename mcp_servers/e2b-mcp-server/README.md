# E2B MCP Server

A production-ready Model Context Protocol (MCP) server that integrates AI assistants with E2B's sandboxed code execution environment.

## Overview

This MCP server provides secure, sandboxed code execution capabilities for Python and JavaScript, along with file management and package installation features. Built for the Klavis AI coding assignment, it demonstrates enterprise-grade architecture with comprehensive error handling, security validation, and resource management.

## Features

### Core Tools

1. **`execute_python`** - Execute Python code in sandboxed environment
2. **`execute_javascript`** - Execute JavaScript/Node.js code 
3. **`create_file`** - Create files in sandbox
4. **`read_file`** - Read files from sandbox
5. **`list_files`** - List directory contents
6. **`install_packages`** - Install Python (pip) or Node.js (npm) packages
7. **`get_sandbox_info`** - Get sandbox status and resource information

### Key Features

- **Security-First Design**: Input validation, output sanitization, and dangerous pattern detection
- **Resource Management**: Automatic sandbox cleanup, idle timeout handling, and resource monitoring
- **Production Ready**: Comprehensive logging, error handling, and graceful shutdown
- **Multi-language Support**: Both Python and JavaScript execution environments
- **Persistent Sessions**: Reuse sandboxes across tool calls for better performance

## Installation

1. **Clone and Install Dependencies**
   ```bash
   git clone <repository>
   cd my-mcp-server
   npm install
   ```

2. **Set Environment Variables**
   ```bash
   export E2B_API_KEY="your-e2b-api-key"
   export LOG_LEVEL="info"  # Optional: debug, info, warn, error
   export NODE_ENV="production"  # Optional: enables file logging
   ```

3. **Build the Project**
   ```bash
   npm run build
   ```

4. **Test the Installation**
   ```bash
   npm test
   ```

## Usage

### As MCP Server

Configure your MCP client to use this server:

```json
{
  "mcpServers": {
    "e2b-server": {
      "command": "node",
      "args": ["/path/to/my-mcp-server/dist/index.js"],
      "env": {
        "E2B_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Development Mode

```bash
npm run dev
```

### Direct Testing

```bash
# Run comprehensive tests
npm test

# Or run the built server directly
npm start
```

## API Reference

### execute_python

Execute Python code in a sandboxed environment.

**Parameters:**
- `code` (string, required): Python code to execute
- `sandbox_id` (string, optional): Specific sandbox ID to reuse

**Example:**
```python
print("Hello from E2B!")
import numpy as np
data = np.array([1, 2, 3, 4, 5])
print(f"Mean: {np.mean(data)}")
```

### execute_javascript

Execute JavaScript/Node.js code in a sandboxed environment.

**Parameters:**
- `code` (string, required): JavaScript code to execute
- `sandbox_id` (string, optional): Specific sandbox ID to reuse

**Example:**
```javascript
console.log("Hello from Node.js!");
const fs = require('fs');
const data = [1, 2, 3, 4, 5];
const mean = data.reduce((a, b) => a + b) / data.length;
console.log(`Mean: ${mean}`);
```

### create_file

Create a file in the sandbox environment.

**Parameters:**
- `path` (string, required): File path to create
- `content` (string, required): File content
- `sandbox_id` (string, optional): Specific sandbox ID

**Example:**
```json
{
  "path": "data/example.txt",
  "content": "Hello, E2B MCP Server!"
}
```

### read_file

Read a file from the sandbox environment.

**Parameters:**
- `path` (string, required): File path to read
- `sandbox_id` (string, optional): Specific sandbox ID

### list_files

List files in a directory.

**Parameters:**
- `path` (string, optional): Directory path (defaults to current directory)
- `sandbox_id` (string, optional): Specific sandbox ID

### install_packages

Install packages in the sandbox environment.

**Parameters:**
- `packages` (array of strings, required): Package names to install
- `language` (string, required): "python" or "javascript"
- `sandbox_id` (string, optional): Specific sandbox ID

**Examples:**
```json
{
  "packages": ["numpy", "pandas", "matplotlib"],
  "language": "python"
}
```

```json
{
  "packages": ["lodash", "axios", "moment"],
  "language": "javascript"
}
```

### get_sandbox_info

Get information about sandbox status and resource usage.

**Parameters:**
- `sandbox_id` (string, optional): Specific sandbox ID (if not provided, lists all sandboxes)

## Security Features

### Input Validation
- Code length limits (50KB max)
- Dangerous pattern detection
- Package name validation
- File path sanitization

### Output Sanitization
- ANSI escape code removal
- Secret detection and masking
- Output length limits (10KB max)

### Resource Limits
- Execution timeout (30 seconds)
- Idle sandbox cleanup (5 minutes)
- Maximum file size (10MB)
- Package installation limits

### Dangerous Pattern Detection
The server monitors for potentially dangerous patterns:
- Network operations (`socket`, `requests`, `fetch`)
- System file access (`/etc`, `/root`, `/sys`)
- Process operations (`subprocess`, `child_process`)
- Secret patterns (API keys, passwords)

## Architecture

### Core Components

1. **SandboxService** (`src/sandbox-manager.ts`)
   - Manages E2B sandbox lifecycle
   - Handles resource cleanup and idle timeouts
   - Provides sandbox pooling and reuse

2. **E2BTools** (`src/tools.ts`)
   - Implements all MCP tool handlers
   - Integrates with E2B API
   - Handles execution and file operations

3. **SecurityValidator** (`src/security.ts`)
   - Input validation and sanitization
   - Pattern detection for dangerous code
   - Output sanitization and secret masking

4. **Logger** (`src/logger.ts`)
   - Structured logging with Winston
   - Development and production configurations
   - Security event logging

### Error Handling

- Comprehensive try-catch blocks
- Graceful degradation
- Detailed error logging
- User-friendly error messages
- Automatic resource cleanup on failures

### Resource Management

- Automatic sandbox cleanup on idle timeout
- Graceful shutdown handlers
- Memory and resource monitoring
- Connection pooling for better performance

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `E2B_API_KEY` | Yes | - | Your E2B API key |
| `LOG_LEVEL` | No | info | Logging level (debug, info, warn, error) |
| `NODE_ENV` | No | development | Environment (enables file logging in production) |

## Development

### Project Structure

```
src/
├── index.ts           # Main MCP server entry point
├── sandbox-manager.ts # E2B sandbox lifecycle management
├── tools.ts          # MCP tool implementations
├── security.ts       # Security validation and sanitization
├── logger.ts         # Logging configuration
├── types.ts          # TypeScript type definitions
└── test.ts           # Comprehensive test suite
```

### Building

```bash
npm run build
```

### Testing

```bash
# Mock tests (no API key required) - verify implementation structure
npm run test-mock

# Full functionality tests (requires E2B_API_KEY environment variable)
npm test
```

**Mock Testing:**
The `test-mock` script verifies that your implementation is structurally correct without requiring an E2B API key. This is useful for:
- Verifying tool definitions are correct
- Checking method signatures
- Testing implementation structure
- CI/CD environments where API keys aren't available

**Full Testing:**
The `test` script runs comprehensive functionality tests including:
- Python code execution
- JavaScript code execution  
- File operations (create, read, list)
- Package installation (Python & JavaScript)
- Sandbox management
- Error handling

### Linting and Type Checking

```bash
npx tsc --noEmit
```

## Production Deployment

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
ENV NODE_ENV=production
CMD ["npm", "start"]
```

### Environment Setup

```bash
# Production environment variables
export NODE_ENV=production
export LOG_LEVEL=info
export E2B_API_KEY=your-production-api-key
```

### Monitoring

The server provides structured JSON logging suitable for log aggregation services:

```json
{
  "level": "info",
  "message": "Executing Python code in sandbox abc-123",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "e2b-mcp-server"
}
```

## Performance Considerations

- **Sandbox Reuse**: Sandboxes are reused across tool calls to reduce latency
- **Idle Cleanup**: Automatic cleanup after 5 minutes of inactivity
- **Output Limits**: Output is truncated at 10KB to prevent memory issues  
- **Timeout Management**: 30-second execution timeout with graceful error handling
- **Resource Monitoring**: Built-in sandbox resource usage tracking

## Troubleshooting

### Common Issues

1. **"E2B_API_KEY environment variable is required"**
   - Ensure your E2B API key is set in environment variables
   - Verify the key is valid and has appropriate permissions

2. **"Sandbox creation failed"**
   - Check E2B service status
   - Verify API key permissions  
   - Check network connectivity

3. **"Security validation failed"**
   - Review code for dangerous patterns
   - Check file paths for directory traversal
   - Verify package names follow naming conventions

4. **"Execution timeout"**
   - Code took longer than 30 seconds to execute
   - Consider optimizing code or breaking into smaller chunks

### Fixed Issues (Latest Update)

**✅ Code Execution Issue Resolved**

The previous issue with Jupyter kernel port (49999) not being open has been **completely resolved**. The server now uses E2B's latest v1.5.1 SDK which provides direct code execution without relying on Jupyter kernels.

**What was fixed:**
- Updated from legacy Jupyter-based execution to E2B's modern code execution API
- Fixed `execute_python` ✅ - Now works with E2B v1.5.1 direct execution
- Fixed `execute_javascript` ✅ - Now works with proper Node.js wrapping  
- Fixed `install_packages` ✅ - Now works for both Python (pip) and JavaScript (npm)

**All features now working:**
- ✅ `execute_python` - Execute Python code in sandboxed environment
- ✅ `execute_javascript` - Execute JavaScript/Node.js code
- ✅ `create_file` - Create files in sandbox
- ✅ `read_file` - Read files from sandbox  
- ✅ `list_files` - List directory contents
- ✅ `install_packages` - Install Python (pip) or Node.js (npm) packages
- ✅ `get_sandbox_info` - Get sandbox status and resource information

### Logging

Enable debug logging for detailed troubleshooting:
```bash
export LOG_LEVEL=debug
npm start
```

## Contributing

This project follows TypeScript strict mode and includes comprehensive error handling. When contributing:

1. Follow the existing code style
2. Add appropriate error handling
3. Include security validation for new features
4. Update tests for new functionality
5. Add logging for important operations

## License

MIT License - see LICENSE file for details.

## Proof of Correctness

As required by Klavis AI submission guidelines, comprehensive proof videos are available demonstrating every tool working with natural language queries:

**🎥 Video Demonstrations**: https://drive.google.com/drive/folders/1jkqqiY7brz0OfGZT3MwDdJRfrzMqq9mc?usp=drive_link

Each video shows:
- Natural language query in Claude Desktop/Cursor
- Correct tool selection and execution
- Server logs confirming functionality
- Successful results returned to AI client

See `proof-videos/README.md` for detailed documentation of each demonstration.

## Support

For issues specific to this MCP server implementation, please check the troubleshooting section above. For E2B-related issues, consult the [E2B documentation](https://e2b.dev/docs).