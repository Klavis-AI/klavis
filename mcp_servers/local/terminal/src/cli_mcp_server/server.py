import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("cli-mcp-server")


class CommandError(Exception):
    """Base exception for command-related errors"""

    pass


class CommandSecurityError(CommandError):
    """Security violation errors"""

    pass


class CommandExecutionError(CommandError):
    """Command execution errors"""

    pass


class CommandTimeoutError(CommandError):
    """Command timeout errors"""

    pass


@dataclass
class SecurityConfig:
    """
    Security configuration for command execution
    """

    allowed_commands: set[str]
    allowed_flags: set[str]
    max_command_length: int
    command_timeout: int
    allow_all_commands: bool = False
    allow_all_flags: bool = False
    allow_shell_operators: bool = False


class CommandExecutor:
    def __init__(self, allowed_dir: str, security_config: SecurityConfig):
        if not allowed_dir or not os.path.exists(allowed_dir):
            raise ValueError("Valid ALLOWED_DIR is required")
        self.allowed_dir = os.path.abspath(os.path.realpath(allowed_dir))
        self.security_config = security_config

    def _normalize_path(self, path: str) -> str:
        """
        Normalizes a path and ensures it's within allowed directory.
        """
        try:
            if os.path.isabs(path):
                # If absolute path, check directly
                real_path = os.path.abspath(os.path.realpath(path))
            else:
                # If relative path, combine with allowed_dir first
                real_path = os.path.abspath(
                    os.path.realpath(os.path.join(self.allowed_dir, path))
                )

            if not self._is_path_safe(real_path):
                raise CommandSecurityError(
                    f"Path '{path}' is outside of allowed directory: {self.allowed_dir}"
                )

            return real_path
        except CommandSecurityError:
            raise
        except Exception as e:
            raise CommandSecurityError(f"Invalid path '{path}': {str(e)}")

    def validate_command(self, command_string: str) -> tuple[str, List[str]]:
        """
        Validates and parses a command string for security and formatting.

        Checks if the command string contains shell operators. If it does, splits the command
        by operators and validates each part individually. If all parts are valid, returns
        the original command string to be executed with shell=True.

        For commands without shell operators, splits into command and arguments and validates
        each part according to security rules.

        Args:
            command_string (str): The command string to validate and parse.

        Returns:
            tuple[str, List[str]]: A tuple containing:
                - For regular commands: The command name (str) and list of arguments (List[str])
                - For commands with shell operators: The full command string and empty args list

        Raises:
            CommandSecurityError: If any part of the command fails security validation.
        """

        # Define shell operators
        shell_operators = ["&&", "||", "|", ">", ">>", "<", "<<", ";"]

        # Check if command contains shell operators
        contains_shell_operator = any(
            operator in command_string for operator in shell_operators
        )

        if contains_shell_operator:
            # Check if shell operators are allowed
            if not self.security_config.allow_shell_operators:
                # If shell operators are not allowed, raise an error
                for operator in shell_operators:
                    if operator in command_string:
                        raise CommandSecurityError(
                            f"Shell operator '{operator}' is not supported. Set ALLOW_SHELL_OPERATORS=true to enable."
                        )

            # Split the command by shell operators and validate each part
            return self._validate_command_with_operators(
                command_string, shell_operators
            )

        # Process single command without shell operators
        return self._validate_single_command(command_string)

    def _is_url_path(self, path: str) -> bool:
        """
        Checks if a given path is a URL of type http or https.

        Args:
            path (str): The path to check.

        Returns:
            bool: True if the path is a URL, False otherwise.
        """
        url_pattern = re.compile(r"^https?://")
        return bool(url_pattern.match(path))

    def _is_path_safe(self, path: str) -> bool:
        """
        Checks if a given path is safe to access within allowed directory boundaries.

        Validates that the absolute resolved path is within the allowed directory
        to prevent directory traversal attacks.

        Args:
            path (str): The path to validate.

        Returns:
            bool: True if path is within allowed directory, False otherwise.
                Returns False if path resolution fails for any reason.

        Private method intended for internal use only.
        """
        try:
            # Resolve any symlinks and get absolute path
            real_path = os.path.abspath(os.path.realpath(path))
            allowed_dir_real = os.path.abspath(os.path.realpath(self.allowed_dir))

            # Check if the path starts with allowed_dir
            return real_path.startswith(allowed_dir_real)
        except Exception:
            return False

    def _validate_single_command(self, command_string: str) -> tuple[str, List[str]]:
        """
        Validates a single command without shell operators.

        Args:
            command_string (str): The command string to validate.

        Returns:
            tuple[str, List[str]]: A tuple containing the command and validated arguments.

        Raises:
            CommandSecurityError: If the command fails validation.
        """
        try:
            parts = shlex.split(command_string)
            if not parts:
                raise CommandSecurityError("Empty command")

            command, args = parts[0], parts[1:]

            # Validate command if not in allow-all mode
            if (
                not self.security_config.allow_all_commands
                and command not in self.security_config.allowed_commands
            ):
                raise CommandSecurityError(f"Command '{command}' is not allowed")

            # Process and validate arguments
            validated_args = []
            for arg in args:
                is_explicit_path = (arg.startswith(("./", "../", "/")) and not arg.startswith("//")) or arg == "."
                
                if arg.startswith("-"):
                    if (
                        not self.security_config.allow_all_flags
                        and arg not in self.security_config.allowed_flags
                    ):
                        raise CommandSecurityError(f"Flag '{arg}' is not allowed")
                    validated_args.append(arg)
                    continue
                # For any path-like argument, validate it
                if is_explicit_path or ("/" in arg and os.path.exists(os.path.join(self.allowed_dir, arg))):
                    if self._is_url_path(arg):
                        # If it's a URL, we don't need to normalize it
                        validated_args.append(arg)
                        continue

                    normalized_path = self._normalize_path(arg)
                    validated_args.append(normalized_path)
                else:
                    # For non-path arguments, add them as-is
                    validated_args.append(arg)

            return command, validated_args

        except ValueError as e:
            raise CommandSecurityError(f"Invalid command format: {str(e)}")

    def _validate_command_with_operators(
        self, command_string: str, shell_operators: List[str]
    ) -> tuple[str, List[str]]:
        """
        Validates a command string that contains shell operators.

        Splits the command string by shell operators and validates each part individually.
        If all parts are valid, returns the original command to be executed with shell=True.

        Args:
            command_string (str): The command string containing shell operators.
            shell_operators (List[str]): List of shell operators to split by.

        Returns:
            tuple[str, List[str]]: A tuple containing the command and empty args list
                                  (since the command will be executed with shell=True)

        Raises:
            CommandSecurityError: If any part of the command fails validation.
        """
        # Create a regex pattern to split by any of the shell operators
        # We need to escape special regex characters in the operators
        escaped_operators = [re.escape(op) for op in shell_operators]
        pattern = "|".join(escaped_operators)

        # Split the command string by shell operators, keeping the operators
        parts = re.split(f"({pattern})", command_string)

        # Filter out empty parts and whitespace-only parts
        parts = [part.strip() for part in parts if part.strip()]

        # Group commands and operators
        commands = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i + 1] in shell_operators:
                # If next part is an operator, current part is a command
                if parts[i]:  # Skip empty commands
                    commands.append(parts[i])
                i += 2  # Skip the operator
            else:
                # If no operator follows, this is the last command
                if (
                    parts[i] and parts[i] not in shell_operators
                ):  # Skip if it's an operator
                    commands.append(parts[i])
                i += 1

        # Validate each command individually
        for cmd in commands:
            try:
                # Use the extracted validation method for each command
                self._validate_single_command(cmd)
            except CommandSecurityError as e:
                raise CommandSecurityError(f"Invalid command part '{cmd}': {str(e)}")
            except ValueError as e:
                raise CommandSecurityError(
                    f"Invalid command format in '{cmd}': {str(e)}"
                )

        # If we get here, all commands passed validation
        # Return the original command string to be executed with shell=True
        return command_string, []

    def execute(self, command_string: str) -> subprocess.CompletedProcess:
        """
        Executes a command string in a secure, controlled environment.

        Runs the command after validating it against security constraints including length limits
        and shell operator restrictions. Executes with controlled parameters for safety.

        Args:
            command_string (str): The command string to execute.

        Returns:
            subprocess.CompletedProcess: The result of the command execution containing
                stdout, stderr, and return code.

        Raises:
            CommandSecurityError: If the command:
                - Exceeds maximum length
                - Fails security validation
                - Fails during execution

        Notes:
            - Uses shell=True for commands with shell operators, shell=False otherwise
            - Uses timeout and working directory constraints
            - Captures both stdout and stderr
        """
        if len(command_string) > self.security_config.max_command_length:
            raise CommandSecurityError(
                f"Command exceeds maximum length of {self.security_config.max_command_length}"
            )

        try:
            command, args = self.validate_command(command_string)

            # Check if this is a command with shell operators
            shell_operators = ["&&", "||", "|", ">", ">>", "<", "<<", ";"]
            use_shell = any(operator in command_string for operator in shell_operators)

            # Double-check that shell operators are allowed if they are present
            if use_shell and not self.security_config.allow_shell_operators:
                for operator in shell_operators:
                    if operator in command_string:
                        raise CommandSecurityError(
                            f"Shell operator '{operator}' is not supported. Set ALLOW_SHELL_OPERATORS=true to enable."
                        )

            if use_shell:
                # For commands with shell operators, execute with shell=True
                return subprocess.run(
                    command,  # command is the full command string in this case
                    shell=True,
                    text=True,
                    capture_output=True,
                    timeout=self.security_config.command_timeout,
                    cwd=self.allowed_dir,
                )
            else:
                # For regular commands, execute with shell=False
                return subprocess.run(
                    [command] + args,
                    shell=False,
                    text=True,
                    capture_output=True,
                    timeout=self.security_config.command_timeout,
                    cwd=self.allowed_dir,
                )
        except subprocess.TimeoutExpired:
            raise CommandTimeoutError(
                f"Command timed out after {self.security_config.command_timeout} seconds"
            )
        except CommandError:
            raise
        except Exception as e:
            raise CommandExecutionError(f"Command execution failed: {str(e)}")


# Load security configuration from environment
def load_security_config() -> SecurityConfig:
    """
    Loads security configuration from environment variables with default fallbacks.

    Creates a SecurityConfig instance using environment variables to configure allowed
    commands, flags, patterns, and execution constraints. Uses predefined defaults if
    environment variables are not set.

    Returns:
        SecurityConfig: Configuration object containing:
            - allowed_commands: Set of permitted command names
            - allowed_flags: Set of permitted command flags/options
            - max_command_length: Maximum length of command string
            - command_timeout: Maximum execution time in seconds
            - allow_all_commands: Whether all commands are allowed
            - allow_all_flags: Whether all flags are allowed
            - allow_shell_operators: Whether shell operators (&&, ||, |, etc.) are allowed

    Environment Variables:
        ALLOWED_COMMANDS: Comma-separated list of allowed commands or 'all' (default: "ls,cat,pwd")
        ALLOWED_FLAGS: Comma-separated list of allowed flags or 'all' (default: "-l,-a,--help")
        MAX_COMMAND_LENGTH: Maximum command string length (default: 1024)
        COMMAND_TIMEOUT: Command timeout in seconds (default: 30)
        ALLOW_SHELL_OPERATORS: Whether to allow shell operators like &&, ||, |, >, etc. (default: false)
                              Set to "true" or "1" to enable, any other value to disable.
    """
    allowed_commands = os.getenv("ALLOWED_COMMANDS", "ls,cat,pwd")
    allowed_flags = os.getenv("ALLOWED_FLAGS", "-l,-a,--help")
    allow_shell_operators_env = os.getenv("ALLOW_SHELL_OPERATORS", "false")

    allow_all_commands = allowed_commands.lower() == "all"
    allow_all_flags = allowed_flags.lower() == "all"
    allow_shell_operators = allow_shell_operators_env.lower() in ("true", "1")

    return SecurityConfig(
        allowed_commands=(
            set() if allow_all_commands else set(allowed_commands.split(","))
        ),
        allowed_flags=set() if allow_all_flags else set(allowed_flags.split(",")),
        max_command_length=int(os.getenv("MAX_COMMAND_LENGTH", "1024")),
        command_timeout=int(os.getenv("COMMAND_TIMEOUT", "30")),
        allow_all_commands=allow_all_commands,
        allow_all_flags=allow_all_flags,
        allow_shell_operators=allow_shell_operators,
    )


executor = CommandExecutor(
    allowed_dir=os.getenv("ALLOWED_DIR", ""), security_config=load_security_config()
)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    commands_desc = (
        "all commands"
        if executor.security_config.allow_all_commands
        else ", ".join(executor.security_config.allowed_commands)
    )
    flags_desc = (
        "all flags"
        if executor.security_config.allow_all_flags
        else ", ".join(executor.security_config.allowed_flags)
    )

    return [
        types.Tool(
            name="run_command",
            description=(
                f"Allows command (CLI) execution in the directory: {executor.allowed_dir}\n\n"
                f"Available commands: {commands_desc}\n"
                f"Available flags: {flags_desc}\n\n"
                f"Shell operators (&&, ||, |, >, >>, <, <<, ;) are {'supported' if executor.security_config.allow_shell_operators else 'not supported'}. Set ALLOW_SHELL_OPERATORS=true to enable."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Single command to execute (example: 'ls -l' or 'cat file.txt')",
                    }
                },
                "required": ["command"],
            },
        ),
        types.Tool(
            name="show_security_rules",
            description=(
                "Show what commands and operations are allowed in this environment.\n"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Optional[Dict[str, Any]]
) -> List[types.TextContent]:
    if name == "run_command":
        if not arguments or "command" not in arguments:
            return [
                types.TextContent(type="text", text="No command provided", error=True)
            ]

        try:
            result = executor.execute(arguments["command"])

            response = []
            if result.stdout:
                response.append(types.TextContent(type="text", text=result.stdout))
            if result.stderr:
                response.append(
                    types.TextContent(type="text", text=result.stderr, error=True)
                )

            response.append(
                types.TextContent(
                    type="text",
                    text=f"\nCommand completed with return code: {result.returncode}",
                )
            )

            return response

        except CommandSecurityError as e:
            return [
                types.TextContent(
                    type="text", text=f"Security violation: {str(e)}", error=True
                )
            ]
        except subprocess.TimeoutExpired:
            return [
                types.TextContent(
                    type="text",
                    text=f"Command timed out after {executor.security_config.command_timeout} seconds",
                    error=True,
                )
            ]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}", error=True)]

    elif name == "show_security_rules":
        commands_desc = (
            "All commands allowed"
            if executor.security_config.allow_all_commands
            else ", ".join(sorted(executor.security_config.allowed_commands))
        )
        flags_desc = (
            "All flags allowed"
            if executor.security_config.allow_all_flags
            else ", ".join(sorted(executor.security_config.allowed_flags))
        )

        security_info = (
            "Security Configuration:\n"
            f"==================\n"
            f"Working Directory: {executor.allowed_dir}\n"
            f"\nAllowed Commands:\n"
            f"----------------\n"
            f"{commands_desc}\n"
            f"\nAllowed Flags:\n"
            f"-------------\n"
            f"{flags_desc}\n"
            f"\nSecurity Limits:\n"
            f"---------------\n"
            f"Max Command Length: {executor.security_config.max_command_length} characters\n"
            f"Command Timeout: {executor.security_config.command_timeout} seconds\n"
        )
        return [types.TextContent(type="text", text=security_info)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cli-mcp-server",
                server_version="0.2.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
