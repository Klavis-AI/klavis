# Google ADK with Klavis MCP Integration

## Create an Agent Project

Run the ADK create command to start a new agent project:

```bash
adk create my_agent
```

## Project Structure

The created agent project has the following structure:

```
my_agent/
    agent.py      # main agent code
    .env          # API keys or project IDs
    __init__.py
```

## Update Your Agent

The `agent.py` file contains a `root_agent` definition which is the only required element of an ADK agent. 

Add MCP tools via Klavis by creating a Strata server and connecting it to the agent using `McpToolset` with `StreamableHTTPConnectionParams`. See [`agent.py`](my_agent/agent.py) for a complete example integrating Gmail and Slack MCP servers.

## Run Your Agent

```bash
adk web
```

This will launch a web interface to interact with your agent.

