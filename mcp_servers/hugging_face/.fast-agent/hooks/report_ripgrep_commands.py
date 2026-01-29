"""
Hook to surface executed ripgrep commands in the final tool response.

Captures rg commands sent through the execute tool and appends a summary
to the last assistant message after the turn completes.
"""

from fast_agent.core.logging.logger import get_logger
from fast_agent.hooks.hook_context import HookContext

logger = get_logger(__name__)


def _append_summary_to_message(message, summary: str) -> bool:
    content = getattr(message, "content", None)
    if isinstance(content, list) and content:
        for block in reversed(content):
            if isinstance(block, dict) and block.get("type") == "text":
                block["text"] = f"{block.get('text', '')}{summary}"
                return True
            if (
                hasattr(block, "type")
                and getattr(block, "type") == "text"
                and hasattr(block, "text")
            ):
                block.text = f"{getattr(block, 'text', '')}{summary}"
                return True

    if isinstance(content, list):
        content.append({"type": "text", "text": summary})
        return True

    return False


async def add_ripgrep_commands_to_output(ctx: HookContext) -> None:
    if ctx.hook_type != "after_turn_complete":
        return

    rg_commands = getattr(ctx.runner, "_rg_commands", None)
    if not rg_commands:
        return

    commands = sorted(rg_commands)

    summary = "\n\nExecuted rg command(s):\n" + "\n".join(
        f"- `{command}`" for command in commands
    )

    if _append_summary_to_message(ctx.message, summary):
        return

    logger.debug("Appending rg command summary as a new assistant message")
    ctx.runner.append_messages(summary)
