# Contributing to Snowflake MCP Server

Thank you for your interest in contributing to the Snowflake MCP Server! This document provides guidelines and instructions for contributing to this project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Tool Development Guidelines](#tool-development-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation Guidelines](#documentation-guidelines)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ (≤3.12 recommended)
- Git
- Snowflake account (for testing)
- `uv` or `pip` for dependency management

### Development Setup

1. **Clone the repository**:

```bash
git clone https://github.com/Klavis-AI/klavis.git
cd mcp-snowflake-server
```

2. **Set up development environment**:

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

3. **Configure test environment**:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Snowflake credentials
nano .env
```

4. **Verify setup**:

```bash
# Run the server locally
uv run mcp_snowflake_server --help

# Run tests
pytest

# Run type checking
pyright src/
```

## 📝 Code Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all function parameters and return values

### Code Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
pyright src/
```

### Naming Conventions

- **Tools**: Use descriptive, prefixed names (e.g., `snowflake_list_databases`)
- **Functions**: Use snake_case
- **Constants**: Use UPPER_SNAKE_CASE
- **Classes**: Use PascalCase

## 🛠️ Tool Development Guidelines

When adding new tools to the MCP server, follow these Klavis AI guidelines:

### 1. Tool Atomicity

Each tool should perform **one specific function**:

✅ **Good**: `snowflake_get_table_row_count`
❌ **Bad**: `snowflake_analyze_table_comprehensive`

### 2. Clear Naming & Descriptions

Tool names and descriptions should be AI-friendly:

```python
Tool(
    name="snowflake_check_table_exists",
    description="Check if a specific table exists in Snowflake. Returns boolean result indicating table existence. Use this before querying tables to avoid errors.",
    # ... rest of tool definition
)
```

### 3. Robust Error Handling

Provide helpful error messages that AI can understand:

```python
async def handle_my_tool(arguments, db, *_):
    try:
        # Tool logic here
        pass
    except Exception as e:
        if "does not exist" in str(e).lower():
            raise ValueError(f"Table not found: {str(e)}. Use snowflake_list_tables to discover available tables.")
        else:
            raise ValueError(f"Operation failed: {str(e)}")
```

### 4. Input Validation

Always validate inputs and provide clear error messages:

```python
if not arguments or "table_name" not in arguments:
    raise ValueError("Missing required parameter: table_name")

if len(table_name.split(".")) != 3:
    raise ValueError("Table name must be fully qualified as 'database.schema.table'")
```

### 5. Structured Output

Return consistent, structured responses:

```python
output = {
    "type": "operation_result",
    "data_id": data_id,
    "metadata": metadata,
    "data": results,
}
yaml_output = to_yaml(output)
json_output = to_json(output)
return [
    types.TextContent(type="text", text=yaml_output),
    types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=f"data://{data_id}",
            text=json_output,
            mimeType="application/json"
        ),
    ),
]
```

## 🧪 Testing Requirements

### Test Coverage

All new tools must include:

1. **Unit tests** for the tool function
2. **Integration tests** with real Snowflake connection
3. **Error handling tests** for invalid inputs
4. **Documentation tests** in TESTING.md

### Test Structure

```python
# tests/test_tools.py
import pytest
from src.mcp_snowflake_server.server import handle_my_new_tool

@pytest.mark.asyncio
async def test_my_new_tool_success(mock_db):
    """Test successful tool execution"""
    arguments = {"param": "valid_value"}
    result = await handle_my_new_tool(arguments, mock_db)
    assert len(result) == 2  # TextContent + EmbeddedResource
    assert "success_indicator" in result[0].text

@pytest.mark.asyncio
async def test_my_new_tool_invalid_input(mock_db):
    """Test error handling for invalid input"""
    arguments = {}  # Missing required parameter
    with pytest.raises(ValueError, match="Missing required parameter"):
        await handle_my_new_tool(arguments, mock_db)
```

### Manual Testing

Document manual testing in TESTING.md with:

- Natural language query
- Expected tool call
- Sample successful result
- Error cases

Example:

```markdown
### snowflake_my_new_tool

#### Test Case: Successful Operation

**Query**: "Perform my new operation on the CUSTOMERS table"
**Expected Tool Call**: `snowflake_my_new_tool`
**Parameters**: `{"table_name": "ANALYTICS_DB.PUBLIC.CUSTOMERS"}`
**Sample Result**: [Expected output here]
**✅ Status**: PASS - Tool correctly invoked and executed
```

## 🔄 Pull Request Process

### Before Submitting

1. **Run all tests**: Ensure all tests pass locally
2. **Update documentation**: Include TESTING.md entries for new tools
3. **Check code quality**: Run linting and type checking
4. **Test manually**: Verify tools work with Claude Desktop

### PR Checklist

- [ ] **Code follows style guidelines**
- [ ] **All tests pass**
- [ ] **New tools documented in TESTING.md**
- [ ] **README updated if needed**
- [ ] **Type hints added for all new functions**
- [ ] **Error messages are AI-friendly**
- [ ] **Tools are atomic and well-named**

### PR Template

Use this template for your pull request:

```markdown
## Description

Brief description of changes made.

## Type of Change

- [ ] Bug fix
- [ ] New tool/feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## New Tools Added

List any new tools with their purpose:

- `snowflake_tool_name`: Description of what it does

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] TESTING.md updated

## Documentation

- [ ] README updated
- [ ] TESTING.md updated
- [ ] Code comments added
- [ ] Type hints added

## Breaking Changes

List any breaking changes and migration path.
```

## 📚 Documentation Guidelines

### Code Documentation

- Use clear, descriptive docstrings
- Include parameter types and descriptions
- Document error conditions
- Provide usage examples

```python
async def handle_my_tool(arguments, db, write_detector, *_):
    """
    Handle my_tool operation to perform specific Snowflake task.

    Args:
        arguments: Dict containing tool parameters
            - table_name (str): Fully qualified table name
            - limit (int, optional): Number of results to return
        db: SnowflakeDB instance for database operations
        write_detector: SQLWriteDetector for query analysis

    Returns:
        List of TextContent and EmbeddedResource with operation results

    Raises:
        ValueError: If table_name is missing or invalid format

    Example:
        arguments = {"table_name": "DB.SCHEMA.TABLE", "limit": 10}
        result = await handle_my_tool(arguments, db, write_detector)
    """
```

### README Updates

When adding new tools, update the README.md:

1. Add tool to the "Available Tools" section
2. Include clear description and usage examples
3. Update any relevant configuration sections

### TESTING.md Updates

For each new tool, add comprehensive testing documentation showing:

- Natural language query examples
- Expected tool invocations
- Sample successful results
- Error handling demonstrations

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment details**: Python version, Snowflake setup
2. **Reproduction steps**: Exact steps to reproduce the issue
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Full error messages and stack traces
6. **Configuration**: Relevant configuration details (no credentials!)

## 💡 Feature Requests

When requesting new features:

1. **Use case**: Describe the specific use case
2. **Current workaround**: How you currently solve this (if any)
3. **Proposed solution**: Your suggested approach
4. **Alternatives**: Other approaches you've considered

## 🤝 Community Guidelines

- **Be respectful**: Treat all contributors with respect
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Maintainers and contributors are volunteers
- **Follow the code of conduct**: Adhere to project standards

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check README.md and TESTING.md first

## 🎯 Development Priorities

Current priorities for contributions:

1. **Additional Snowflake Tools**: More atomic operations
2. **Performance Improvements**: Query optimization and caching
3. **Error Handling**: Better error messages and recovery
4. **Documentation**: More examples and use cases
5. **Testing**: Expanded test coverage

Thank you for contributing to the Snowflake MCP Server! 🎉
