"""Command-line interface for Strata MCP Router using argparse."""

import argparse
import os
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

from strata.mcp_client_manager import MCPClientManager

from .config import MCPServerConfig, MCPServerList
from .logging_config import setup_logging
from .server import run_server, run_stdio_server
from .utils.tool_integration import add_strata_to_tool


def add_command(args):
    """Add a new MCP server configuration."""
    server_list = MCPServerList(args.config_path)

    # Normalize type (command is alias for stdio)
    server_type = args.type
    if server_type == "command":
        server_type = "stdio"

    # Parse environment variables
    env_dict = {}
    if args.env:
        for env_var in args.env:
            if "=" not in env_var:
                print(
                    f"Error: Invalid environment variable format: {env_var}",
                    file=sys.stderr,
                )
                print(
                    "Environment variables must be in KEY=VALUE format", file=sys.stderr
                )
                return 1
            key, value = env_var.split("=", 1)
            env_dict[key.strip()] = value

    # Parse headers for URL type
    headers_dict = {}
    if args.header:
        for header_var in args.header:
            if ":" not in header_var:
                print(f"Error: Invalid header format: {header_var}", file=sys.stderr)
                print("Headers must be in KEY:VALUE format", file=sys.stderr)
                return 1
            key, value = header_var.split(":", 1)
            headers_dict[key.strip()] = value.strip()

    if server_type in ["sse", "http"]:
        # Parse HTTP URL to extract base URL and any query parameters
        parsed = urlparse(args.url_or_command)

        # Reconstruct URL without query parameters for the URL field
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.path == "" or parsed.path == "/":
            base_url = f"{parsed.scheme}://{parsed.netloc}"

        auth = args.auth_type[0] if args.auth_type else ""
        config = MCPServerConfig(
            name=args.name,
            type=server_type,
            url=base_url,
            headers=headers_dict,
            env=env_dict,
            enabled=args.enabled,
            auth=auth
        )
    else:  # stdio/command
        # For stdio, url_or_command is the command, args.args contains the arguments
        config = MCPServerConfig(
            name=args.name,
            type="stdio",
            command=args.url_or_command,
            args=args.args if args.args else [],
            env=env_dict,
            enabled=args.enabled,
        )

    # Add server to configuration
    if server_list.add_server(config):
        server_list.save()
        print(f"✓ Successfully added server '{args.name}' with {server_type} type")
    else:
        print(f"Server '{args.name}' already exists with identical configuration")

    return 0


def remove_command(args):
    """Remove an MCP server configuration."""
    server_list = MCPServerList(args.config_path)

    if args.name in server_list.servers:
        del server_list.servers[args.name]
        server_list.save()
        print(f"✓ Successfully removed server '{args.name}'")
        return 0
    else:
        print(f"Error: Server '{args.name}' not found", file=sys.stderr)
        return 1


def list_command(args):
    """List all configured MCP servers."""
    server_list = MCPServerList(args.config_path)

    if not server_list.servers:
        print("No servers configured")
        return 0

    print("Configured MCP servers:")
    for name, config in server_list.servers.items():
        status = "enabled" if config.enabled else "disabled"
        type_str = config.type or "stdio"

        if type_str in ["sse", "http"]:
            location = config.url
        else:
            location = f"{config.command} {' '.join(config.args or [])}"

        print(f"  • {name} ({type_str}, {status}): {location}")

    return 0


def enable_command(args):
    """Enable an MCP server."""
    server_list = MCPServerList(args.config_path)

    if args.name not in server_list.servers:
        print(f"Error: Server '{args.name}' not found", file=sys.stderr)
        return 1

    server_list.servers[args.name].enabled = True
    server_list.save()
    print(f"✓ Enabled server '{args.name}'")
    return 0


def disable_command(args):
    """Disable an MCP server."""
    server_list = MCPServerList(args.config_path)

    if args.name not in server_list.servers:
        print(f"Error: Server '{args.name}' not found", file=sys.stderr)
        return 1

    server_list.servers[args.name].enabled = False
    server_list.save()
    print(f"✓ Disabled server '{args.name}'")
    return 0

async def authenticate(server_name):
    # Only initialize the specific server we want to authenticate
    async with MCPClientManager(server_names=[server_name]) as client_manager:
        await client_manager.authenticate_server(server_name)

def authenticate_command(args):
    """Authenticate with an OAuth2 provider for a given MCP server URL."""
    server_list = MCPServerList(args.config_path)

    if args.name in server_list.servers:
        asyncio.run(authenticate(args.name))
        return 0
    else:
        print(f"Error: Server '{args.name}' not found", file=sys.stderr)
        return 1

def tool_add_command(args):
    """Add Strata MCP server to Claude, Gemini, VSCode, or Cursor configurations."""
    return add_strata_to_tool(args.target, args.scope or "user")


def run_command(args):
    """Run the Strata MCP router."""
    # Initialize server with config path if provided
    if args.config_path:
        import os

        os.environ["MCP_CONFIG_PATH"] = str(args.config_path)

    if args.port is not None:
        # Server mode with HTTP/SSE
        print(f"Starting Strata MCP Router server on port {args.port}...")
        return run_server(
            args.port, json_response=False
        )
    else:
        # Stdio mode
        print("Starting Strata MCP Router in stdio mode...", file=sys.stderr)
        return run_stdio_server()


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="strata", description="Strata MCP Router - Manage and run MCP servers"
    )

    # Global options
    # Check environment variables for default config path
    default_config_path = os.environ.get("STRATA_CONFIG_PATH")
    parser.add_argument(
        "--config-path",
        type=Path,
        default=Path(default_config_path) if default_config_path else None,
        help="Path to configuration file (default: $STRATA_CONFIG_PATH or $MCP_CONFIG_PATH or ~/.config/strata/servers.json)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command - use REMAINDER to capture all remaining args including those starting with -
    add_parser = subparsers.add_parser("add", help="Add a new MCP server configuration")
    add_parser.add_argument(
        "--type",
        choices=["sse", "http", "stdio", "command"],
        required=True,
        help="Type of the MCP server (sse/http for URL-based, stdio/command for process)",
    )
    add_parser.add_argument(
        "--env", action="append", help="Environment variables in KEY=VALUE format"
    )
    add_parser.add_argument(
        "--header",
        action="append",
        help="HTTP headers in KEY:VALUE format (for URL type only)",
    )
    add_parser.add_argument(
        "--auth_type",
        action="append",
        help="Authentication type (oauth etc.)",
    )
    add_parser.add_argument(
        "--enabled/--disabled",
        dest="enabled",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Whether the server is enabled by default",
    )
    add_parser.add_argument("name", help="Name of the server")
    add_parser.add_argument(
        "url_or_command", help="URL for HTTP/SSE or command for stdio"
    )
    add_parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for stdio command (use -- before args starting with -)",
    )
    add_parser.set_defaults(func=add_command)

    # Remove command
    remove_parser = subparsers.add_parser(
        "remove", help="Remove an MCP server configuration"
    )
    remove_parser.add_argument("name", help="Name of the server to remove")
    remove_parser.set_defaults(func=remove_command)

    # List command
    list_parser = subparsers.add_parser("list", help="List all configured MCP servers")
    list_parser.set_defaults(func=list_command)

    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable an MCP server")
    enable_parser.add_argument("name", help="Name of the server to enable")
    enable_parser.set_defaults(func=enable_command)

    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable an MCP server")
    disable_parser.add_argument("name", help="Name of the server to disable")
    disable_parser.set_defaults(func=disable_command)

    # Authenticate command
    auth_parser = subparsers.add_parser("auth", help="Authenticate with an MCP server")
    auth_parser.add_argument("name", help="Name of the server to authenticate with")
    auth_parser.set_defaults(func=authenticate_command)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the Strata MCP router")
    run_parser.add_argument(
        "--port",
        type=int,
        help="Port to listen on for HTTP/SSE server mode. If not provided, runs in stdio mode.",
    )
    run_parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    run_parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Skip displaying the banner on startup",
    )
    run_parser.set_defaults(func=run_command)

    # Set run as default command when no subcommand is provided
    parser.set_defaults(
        command="run", func=run_command, port=None, log_level="INFO", no_banner=False
    )

    # Tool command
    tool_parser = subparsers.add_parser("tool", help="Tool integration commands")
    tool_subparsers = tool_parser.add_subparsers(
        dest="tool_command", help="Tool commands"
    )

    # Tool add command
    tool_add_parser = tool_subparsers.add_parser(
        "add", help="Add Strata to Claude, Gemini, VSCode, or Cursor MCP configuration"
    )
    tool_add_parser.add_argument(
        "target",
        choices=["claude", "gemini", "vscode", "cursor"],
        help="Target CLI to add Strata to (claude, gemini, vscode, or cursor)",
    )
    tool_add_parser.add_argument(
        "--scope",
        choices=["user", "project", "local"],
        default="user",
        help="Configuration scope (user, project, or local). Default: user. Note: VSCode doesn't support scope.",
    )
    tool_add_parser.set_defaults(func=tool_add_command)

    return parser


def main():
    """Main entry point for the MCP Router."""
    parser = create_parser()
    args = parser.parse_args()

    # Initialize logging with appropriate settings
    log_level = getattr(args, "log_level", "INFO")
    no_banner = getattr(args, "no_banner", False)
    # banner is only relevant when running the server
    if args.command != "run":
        no_banner = True
    setup_logging(log_level, no_banner)

    # If no subcommand provided, show help
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    # Handle tool subcommand specially
    if args.command == "tool" and not hasattr(args, "func"):
        # No tool subcommand provided, show help message
        print("Error: No tool subcommand provided", file=sys.stderr)
        print("\nAvailable tool commands:")
        print("  add    Add Strata to Claude, Gemini, or VSCode MCP configuration")
        print("\nUse 'strata tool <command> --help' for more information on a command.")
        return 1

    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
