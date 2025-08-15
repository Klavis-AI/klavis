import argparse
import asyncio
import os
import sys

import dotenv
import snowflake.connector

# Handle TOML imports based on Python version
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from . import server


def load_connection_from_toml(toml_file: str, connection_name: str) -> dict:
    """Load connection configuration from a TOML file.
    
    Args:
        toml_file: Path to the TOML file containing connection configurations
        connection_name: Name of the connection to load from the file
        
    Returns:
        Dictionary containing connection parameters
        
    Raises:
        FileNotFoundError: If the TOML file doesn't exist
        KeyError: If the connection name doesn't exist in the file
        ValueError: If the TOML file is invalid
    """
    try:
        with open(toml_file, 'rb') as f:
            toml_data = tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"TOML file not found: {toml_file}")
    except Exception as e:
        raise ValueError(f"Invalid TOML file: {e}")
    
    # Look for the connection as a top-level section
    if connection_name in toml_data:
        connection_config = toml_data[connection_name]
    else:
        raise KeyError(f"Connection '{connection_name}' not found in TOML file")
    
    return connection_config


def parse_args():
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument(
        "--allow_write", required=False, default=False, action="store_true", help="Allow write operations on the database"
    )
    parser.add_argument("--log_dir", required=False, default=None, help="Directory to log to")
    parser.add_argument("--log_level", required=False, default="INFO", help="Logging level")
    parser.add_argument(
        "--prefetch",
        action="store_true",
        dest="prefetch",
        default=False,
        help="Prefetch table descriptions (when enabled, list_tables and describe_table are disabled)",
    )
    parser.add_argument(
        "--no-prefetch",
        action="store_false",
        dest="prefetch",
        help="Don't prefetch table descriptions",
    )
    parser.add_argument(
        "--exclude_tools",
        required=False,
        default=[],
        nargs="+",
        help="List of tools to exclude",
    )
    
    parser.add_argument(
        "--private_key_path",
        required=False,
        help="Path to private key file for authentication",
    )
    
    parser.add_argument(
        "--connection-name",
        required=False,
        default=None,
        help="Name of the connection to use from the TOML file",
    )
    
    parser.add_argument(
        "--connections-file",
        required=False,
        default=None,
        help="Path to the TOML file containing connection configurations",
    )

    # First, get all the arguments we don't know about
    args, unknown = parser.parse_known_args()

    # Create a dictionary to store our key-value pairs
    connection_args = {}

    # Iterate through unknown args in pairs
    for i in range(0, len(unknown), 2):
        if i + 1 >= len(unknown):
            break

        key = unknown[i]
        value = unknown[i + 1]

        # Make sure it's a keyword argument (starts with --)
        if key.startswith("--"):
            key = key[2:]  # Remove the '--'
            connection_args[key] = value

    # Now we can add the known args to kwargs
    server_args = {
        "allow_write": args.allow_write,
        "log_dir": args.log_dir,
        "log_level": args.log_level,
        "prefetch": args.prefetch,
        "exclude_tools": args.exclude_tools,
        "connection_name": getattr(args, 'connection_name', None),
        "connections_file": getattr(args, 'connections_file', None),
    }

    # Add private_key_path if provided
    if args.private_key_path:
        connection_args["private_key_path"] = args.private_key_path

    return server_args, connection_args


def main():
    """Main entry point for the package."""

    dotenv.load_dotenv()

    default_connection_args = snowflake.connector.connection.DEFAULT_CONFIGURATION

    connection_args_from_env = {
        k: os.getenv("SNOWFLAKE_" + k.upper())
        for k in default_connection_args
        if os.getenv("SNOWFLAKE_" + k.upper()) is not None
    }

    # Add private key path from environment if available
    private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path:
        connection_args_from_env["private_key_path"] = private_key_path

    server_args, connection_args = parse_args()

    # Check if TOML configuration is requested
    if server_args.get("connections_file") and server_args.get("connection_name"):
        connections_file = server_args["connections_file"]
        connection_name = server_args["connection_name"]
        
        try:
            toml_connection_args = load_connection_from_toml(connections_file, connection_name)
            # TOML config takes precedence, then command line args, then environment variables
            connection_args = {**connection_args_from_env, **connection_args, **toml_connection_args}
        except (FileNotFoundError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to load TOML configuration: {e}")
    
    elif server_args.get("connections_file") or server_args.get("connection_name"):
        # If only one of the TOML parameters is provided, show an error
        raise ValueError("Both --connections-file and --connection-name must be provided together")
    
    else:
        # Use traditional configuration method
        connection_args = {**connection_args_from_env, **connection_args}

    assert (
        "database" in connection_args
    ), 'You must provide the database as "--database" argument, "SNOWFLAKE_DATABASE" environment variable, or in the TOML file.'
    assert (
        "schema" in connection_args
    ), 'You must provide the schema as "--schema" argument, "SNOWFLAKE_SCHEMA" environment variable, or in the TOML file.'

    asyncio.run(
        server.main(
            connection_args=connection_args,
            allow_write=server_args["allow_write"],
            log_dir=server_args["log_dir"],
            prefetch=server_args["prefetch"],
            log_level=server_args["log_level"],
            exclude_tools=server_args["exclude_tools"],
        )
    )


# Optionally expose other important items at package level
__all__ = ["main", "server", "write_detector"]

if __name__ == "__main__":
    main()
