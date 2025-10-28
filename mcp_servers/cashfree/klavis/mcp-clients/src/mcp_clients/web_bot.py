import asyncio
import json
import logging
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from mcp_clients.base_bot import BotContext, BaseBot
from mcp_clients.config import USE_PRODUCTION_DB
from mcp_clients.llms.base import ChatMessage, Conversation, MessageRole, TextContent
from mcp_clients.mcp_client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("web_bot")

# Create FastAPI app
app = FastAPI(title="MCP Web Client API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Model definitions
class QueryRequest(BaseModel):
    user_id: str
    query: str
    conversation_id: Optional[str] = (
        None  # Replacing channel_id with optional conversation_id
    )


class WebBotContext(BotContext):
    """
    Web-specific context for the bot operations.
    Extends the base BotContext with web-specific attributes.
    """

    def __init__(
            self,
            platform_name: str,
            user_id: str,
            conversation_id: Optional[str] = None,
            user_message: Any = None,
    ):
        """
        Initialize the Web bot context.

        Args:
            platform_name: Name of the platform ('web')
            user_id: Web user ID
            conversation_id: Optional conversation ID for tracking web sessions
            user_message: Optional user message object
        """
        super().__init__(
            platform_name=platform_name, user_id=user_id, user_message=user_message
        )
        self.conversation_id = conversation_id

    def get_channel_id(self) -> Optional[str]:
        """
        Get the channel ID for the current context.
        For web bot, we use the user_id as channel_id if no conversation_id is provided.

        Returns:
            String representation of the channel ID
        """
        return None

    def get_thread_id(self) -> Optional[str]:
        """
        Get the thread ID for the current context, if applicable.
        For web bot, we don't use thread_id.

        Returns:
            None for web bot
        """
        return None


class WebBot(BaseBot):
    """
    Web-specific implementation of the bot.
    Extends the base bot with Web-specific functionality.
    """

    def __init__(self):
        """
        Initialize the Web bot.
        """
        super().__init__(platform_name="web_bot")

        # Add user lock to prevent concurrent message processing
        self.user_locks = {}

    async def send_message(
            self,
            context: WebBotContext,
            message: str,
    ) -> Any:
        """
        Send a message via web API.
        For the web bot, messages are sent via SSE stream.

        Args:
            context: Web bot context
            message: Message text to send

        Returns:
            Message object
        """
        # In the web bot, messages are streamed via SSE
        # This method is mainly used for error reporting
        logger.info(f"Web message: {message[:100]}...")
        return {"message": message}

    async def process_query_with_streaming(
            self,
            mcp_client: MCPClient,
            messages_history: List[ChatMessage],
            context: WebBotContext,
    ) -> StreamingResponse:
        """
        Process a query with streaming in web-specific way.
        Returns a StreamingResponse object containing an async generator that yields SSE messages.

        Args:
            mcp_client: MCP client instance
            messages_history: List of previous messages
            context: Web bot context for the interaction

        Returns:
            StreamingResponse object for SSE streaming
        """

        async def stream_generator():
            try:
                async with asyncio.timeout(200):
                    async for chunk in mcp_client.process_query_stream(
                            messages_history,
                            self.store_new_messages if USE_PRODUCTION_DB else None,
                    ):
                        # Check if this is a special message
                        if "<special>" in chunk:
                            # Extract the special message content
                            special_content = chunk.split("<special>")[1].strip()
                            yield f"data: {json.dumps({'type': 'special', 'content': special_content})}\n\n"
                        else:
                            # Regular message
                            yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"

                    # Send done event to signal end of stream
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                logger.error(f"Error processing query stream: {e}", exc_info=True)
                # Yield error message within the stream
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"  # Ensure done event is sent even on error

        # Return the StreamingResponse directly
        return StreamingResponse(
            content=stream_generator(), media_type="text/event-stream"
        )

    async def get_messages_history(
            self, conversation: Conversation, context: WebBotContext, limit: int = 6
    ) -> List[ChatMessage]:
        """
        Get the previous messages for the conversation.
        For web bot, we'll retrieve message history from the database.

        Args:
            context: Web bot context
            limit: Maximum number of previous messages to retrieve

        Returns:
            List of ChatMessage objects representing previous messages
        """

        if USE_PRODUCTION_DB:
            from mcp_clients.database.database import get_messages_for_conversation

            # Get the messages from the conversation
            # Limit the number of messages, considering the tool calls, we multiply by 3
            messages = await get_messages_for_conversation(conversation.id, limit * 3)

            messages.append(
                ChatMessage(
                    role=MessageRole.USER,
                    content=[TextContent(text=context.user_message)],
                )
            )

            return messages
        else:
            # Return user query when database not in use
            logger.info("Database operations skipped: get_messages_history")
            return [
                ChatMessage(
                    role=MessageRole.USER,
                    content=[TextContent(text=context.user_message)],
                )
            ]

    async def run(self):
        """
        Run the web bot.
        For web bot, this is a no-op as FastAPI app is started separately.
        """
        logger.info("Web bot running within FastAPI server")
        pass


# Initialize the bot
web_bot = WebBot()


# FastAPI routes
@app.post("/api/query")
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Process a user query and respond with a streaming response.
    """
    user_id = request.user_id

    # Create context
    context = WebBotContext(
        platform_name="web_bot",
        user_id=user_id,
        conversation_id=request.conversation_id,
        user_message=request.query,
    )

    # Check if user already has a request in progress
    if user_id not in web_bot.user_locks:
        web_bot.user_locks[user_id] = asyncio.Lock()

    if web_bot.user_locks[user_id].locked():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Another request is already being processed for this user",
        )

    # Process with a lock
    async def process_with_lock():
        try:
            async with asyncio.timeout(200), web_bot.user_locks[user_id]:
                try:
                    # Verify user
                    verification_result = await web_bot.verify_user(context)

                    if not verification_result["connected"]:
                        return StreamingResponse(
                            content=[
                                f"data: {json.dumps({'type': 'error', 'content': 'User not connected or verified'})}\n\n"
                            ],
                            media_type="text/event-stream",
                        )

                    # Set MCP client ID and LLM ID from verification result
                    context.mcp_client_id = verification_result["mcp_client_id"]
                    context.llm_id = verification_result["llm_id"]

                    # Get server URLs
                    server_urls = await web_bot.get_server_urls(context)

                    if not server_urls:
                        return StreamingResponse(
                            content=[
                                f"data: {json.dumps({'type': 'error', 'content': 'Not connected to any MCP server'})}\n\n"
                            ],
                            media_type="text/event-stream",
                        )

                    # Check usage limit
                    usage_under_limit = await web_bot.check_and_update_usage_limit(
                        context
                    )
                    if not usage_under_limit:
                        return StreamingResponse(
                            content=[
                                f"data: {json.dumps({'type': 'error', 'content': 'Usage limit reached'})}\n\n"
                            ],
                            media_type="text/event-stream",
                        )
                    mcp_client = await web_bot.initialize_mcp_client(
                        context=context, server_urls=server_urls
                    )
                    messages_history = await web_bot.get_messages_history(
                        conversation=mcp_client.conversation,
                        context=context,
                    )

                    response = await web_bot.process_query_with_streaming(
                        mcp_client, messages_history, context
                    )

                    background_tasks.add_task(mcp_client.cleanup)

                    # If process_query returned None (e.g., due to setup error handled in base class),
                    # return a generic error response.
                    if response is None:
                        logger.error(
                            "process_query returned None, indicating an error during setup."
                        )
                        return StreamingResponse(
                            content=[
                                f"data: {json.dumps({'type': 'error', 'content': 'Failed to process query due to internal error'})}\n\n"
                            ],
                            media_type="text/event-stream",
                        )

                    return response
                except Exception as e:
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    return StreamingResponse(
                        content=[
                            f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                        ],
                        media_type="text/event-stream",
                    )
        except asyncio.TimeoutError:
            logger.warning(
                f"Processing timed out for user {user_id} after 200 seconds. Lock released."
            )
            return StreamingResponse(
                content=[
                    f"data: {json.dumps({'type': 'error', 'content': 'Processing timed out'})}\n\n"
                ],
                media_type="text/event-stream",
            )

    # Start the processing task but don't wait for it
    return await process_with_lock()


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


def main():
    """Run the web bot with uvicorn"""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
