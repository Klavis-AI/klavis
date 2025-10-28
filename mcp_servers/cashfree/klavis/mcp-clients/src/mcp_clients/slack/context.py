"""
Slack bot context module.
"""
from typing import Dict, Any, Optional

from mcp_clients.base_bot import BotContext


class SlackBotContext(BotContext):
    """
    Slack-specific context for the bot operations.
    Extends the base BotContext with Slack-specific attributes.
    """

    def __init__(
            self,
            platform_name: str,
            user_id: str,
            channel_id: str,
            thread_ts: Optional[str] = None,
            initial_message: Optional[Dict[str, Any]] = None,
            user_message: Optional[Dict[str, Any]] = None,
            bot_token: Optional[str] = None,
    ):
        """
        Initialize the Slack bot context.

        Args:
            platform_name: Name of the platform ('slack')
            user_id: Slack user ID
            channel_id: Slack channel ID
            thread_ts: Optional thread timestamp for threading messages
            initial_message: Optional initial message to update
            user_message: Optional user message object
            bot_token: Optional bot token for the request, we need this for init the slack web client
        """
        super().__init__(platform_name, user_id, user_message=user_message)
        self.channel_id = channel_id
        self.thread_ts = thread_ts
        self.initial_message = initial_message
        self.bot_token = bot_token

    def get_channel_id(self) -> Optional[str]:
        """
        Get the channel ID for the current context.
        
        Returns:
            String representation of the channel ID, or None if not applicable
        """
        return str(self.channel_id)

    def get_thread_id(self) -> Optional[str]:
        """
        Get the thread ID for the current context, if applicable.
        
        Returns:
            String representation of the thread ID, or None if not applicable
        """
        return self.thread_ts
