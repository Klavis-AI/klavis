"""
Hook to fix common ripgrep tool call issues.

Fixes two problems that LLMs commonly make:
1. Invalid -R flag in ripgrep commands (rg is recursive by default)
2. Hallucinated tool name variations (exec → execute)

Copy to: .fast-agent/hooks/fix_ripgrep_tool_calls.py
"""

from fast_agent.core.logging.logger import get_logger
from fast_agent.hooks.hook_context import HookContext

logger = get_logger(__name__)


# Map of incorrect tool names to correct ones
TOOL_NAME_CORRECTIONS = {
    "exec": "execute",
    "executescript": "execute",
    "execscript": "execute",
    "executor": "execute",
    "exec_command": "execute",
}


async def fix_ripgrep_tool_calls(ctx: HookContext) -> None:
    """
    Fix common ripgrep agent tool call issues before execution.
    
    1. Strips invalid -R flag from ripgrep commands
    2. Corrects hallucinated tool name variations (exec* → execute)
    """
    if ctx.hook_type != "before_tool_call":
        return
    
    message = ctx.message
    if not message.tool_calls:
        return
    
    for tool_id, tool_call in message.tool_calls.items():
        # Fix 1: Correct hallucinated tool names
        original_name = tool_call.params.name
        
        if original_name in TOOL_NAME_CORRECTIONS:
            corrected_name = TOOL_NAME_CORRECTIONS[original_name]
            tool_call.params.name = corrected_name
            logger.warning(
                "Corrected hallucinated tool name",
                data={"tool_id": tool_id, "original": original_name, "corrected": corrected_name}
            )
        elif original_name.startswith("exec") and original_name != "execute":
            tool_call.params.name = "execute"
            logger.warning(
                "Corrected unknown exec* variant to execute",
                data={"tool_id": tool_id, "original": original_name, "corrected": "execute"}
            )
        
        # Fix 2: Strip -R flag from ripgrep commands
        if tool_call.params.name != "execute":
            continue
        
        args = tool_call.params.arguments
        if not isinstance(args, dict):
            continue
        
        command = args.get("command")
        if not command or not isinstance(command, str) or "rg" not in command:
            continue
        
        modified = False
        original_command = command
        
        # Remove -R flag in various positions
        if " -R " in command:
            command = command.replace(" -R ", " ")
            modified = True
        if command.endswith(" -R"):
            command = command[:-3]
            modified = True
        if " -R\n" in command:
            command = command.replace(" -R\n", "\n")
            modified = True
        
        if modified:
            logger.warning(
                "Stripped invalid -R flag from ripgrep command",
                data={"tool_id": tool_id, "original": original_command, "modified": command}
            )
            args["command"] = command

        # Capture rg commands for summary reporting
        if "rg" in command:
            rg_commands = getattr(ctx.runner, "_rg_commands", None)
            if rg_commands is None:
                rg_commands = set()
                setattr(ctx.runner, "_rg_commands", rg_commands)

            rg_commands.add(command.strip())
