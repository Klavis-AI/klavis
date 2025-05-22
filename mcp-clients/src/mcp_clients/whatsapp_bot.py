import os
import logging
import uvicorn
import time
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, Response
from pywa_async import WhatsApp, types
from pywa_async.types import Message
from dotenv import load_dotenv

from mcp_clients.base_bot import BaseBot, BotContext
from mcp_clients.config import USE_PRODUCTION_DB
from mcp_clients.llms.base import ChatMessage, Conversation, MessageRole, TextContent, FileContent
from mcp_clients.mcp_client import MCPClient

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Environment variables
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
APP_ID = os.environ.get("WHATSAPP_APP_ID")
APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
CALLBACK_URL = os.environ.get("CALLBACK_URL")

# Define long-running tools
LONG_RUNNING_TOOLS = [
    "generate_web_reports",
    "firecrawl_deep_research",
]

# Create FastAPI app
app = FastAPI(title="WhatsApp Bot API")

# Initialize WhatsApp client with ASYNC version
wa = WhatsApp(
    phone_id=PHONE_NUMBER_ID,
    token=ACCESS_TOKEN,
    server=app,
    callback_url=CALLBACK_URL,
    verify_token=VERIFY_TOKEN,
    app_id=APP_ID,
    app_secret=APP_SECRET,
    webhook_challenge_delay=20.0  # Increased delay for webhook challenge
)

class WhatsAppBotContext(BotContext):
    """
    WhatsApp-specific context for the bot operations.
    Extends the base BotContext with WhatsApp-specific attributes.
    """

    def __init__(
            self,
            platform_name: str,
            user_id: str,
            message: Message = None,
            conversation_id: Optional[str] = None,
    ):
        """
        Initialize the WhatsApp bot context.

        Args:
            platform_name: Name of the platform ('whatsapp')
            user_id: WhatsApp user ID (wa_id)
            message: WhatsApp message object
            conversation_id: Optional conversation ID for tracking sessions
        """
        super().__init__(
            platform_name=platform_name, 
            user_id=user_id, 
            user_message=message.text if message else None
        )
        self.message = message
        self.conversation_id = conversation_id

    def get_channel_id(self) -> Optional[str]:
        """
        Get the channel ID for the current context.
        For WhatsApp, we use the user_id as channel_id.

        Returns:
            String representation of the channel ID
        """
        return self.user_id

    def get_thread_id(self) -> Optional[str]:
        """
        Get the thread ID for the current context.
        WhatsApp doesn't have threads, so we return None.

        Returns:
            None as WhatsApp doesn't support threading
        """
        return None


class WhatsAppBot(BaseBot):
    """
    WhatsApp-specific implementation of the bot.
    Extends the base bot with WhatsApp-specific functionality.
    """

    def __init__(self):
        """
        Initialize the WhatsApp bot.
        """
        super().__init__(platform_name="whatsapp")
        
        # Add user lock to prevent concurrent message processing
        self.user_locks = {}

    async def send_message(
            self,
            context: WhatsAppBotContext,
            message: str
    ) -> Any:
        """
        Send a message via WhatsApp.

        Args:
            context: WhatsApp bot context
            message: Message text to send

        Returns:
            Message object or None on failure
        """
        try:
            # Send message via WhatsApp client
            if len(message) > 4096:
                # WhatsApp has a 4096 character limit, so split long messages
                parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
                responses = []
                for part in parts:
                    response = await wa.send_message(
                        to=context.user_id,
                        text=part
                    )
                    responses.append(response)
                return responses[-1]  # Return the last response
            else:
                return await wa.send_message(
                    to=context.user_id,
                    text=message
                )
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None

    async def format_special_message(self, special_content: str) -> str:
        """
        Format special messages for WhatsApp based on their content.
        
        Args:
            special_content: The content of the special message
            
        Returns:
            Formatted message string
        """
        # Parse the special message
        if special_content.startswith("[Calling tool"):
            # Extract tool name and arguments
            try:
                content = special_content.strip("[]")
                tool_parts = content.split("with arguments")
                tool_name = tool_parts[0].replace("Calling tool", "").strip()
                tool_args = tool_parts[1].strip() if len(tool_parts) > 1 else ""
                
                # Create waiting message based on tool type
                waiting_message = "⏳ _Working on your request..._"
                if any(tool in tool_name for tool in LONG_RUNNING_TOOLS):
                    waiting_message = f"⏳ _This tool may take several minutes to complete..._"
                
                # Format for WhatsApp with minimal formatting options
                message = f"""✨ *MCP Server Call*

*Tool:* {tool_name}
*Arguments:* 
```{tool_args[:200]}{'...' if len(tool_args) > 200 else ''}```

{waiting_message}
----------------------------"""
                
                return message
            except Exception as e:
                logger.error(f"Error formatting tool call message: {e}")
                return f"Processing request with tool: {special_content}"
                
        elif "still running" in special_content:
            return f"""⏳ *Tool Still Running*

{special_content.strip('[]')}

_Tool is still running. Please wait..._
----------------------------"""
        
        else:
            return f"""ℹ️ *System Message*

{special_content.strip('[]')}
----------------------------"""

    async def send_special_message(self, context: WhatsAppBotContext, special_content: str) -> Any:
        """
        Handle special messages like tool calls and send formatted responses.
        
        Args:
            context: WhatsApp bot context
            special_content: The content of the special message
            
        Returns:
            Response from WhatsApp API
        """
        try:
            formatted_message = await self.format_special_message(special_content)
            response = await self.send_message(context, formatted_message)
            logger.info(f"Sent special message to {context.user_id}: {special_content[:50]}...")
            return response
        except Exception as e:
            logger.error(f"Error sending special message: {e}")
            return None

    async def process_query_with_streaming(
            self,
            mcp_client: MCPClient,
            messages_history: List[ChatMessage],
            context: WhatsAppBotContext
    ) -> Any:
        """
        Process a query using simple chat completion instead of streaming for WhatsApp.
        WhatsApp doesn't support streamed messages, so we'll wait for the full response.

        Args:
            mcp_client: MCP client instance
            messages_history: List of previous messages
            context: WhatsApp bot context

        Returns:
            Final message object or None
        """
        try:
            # Send a waiting message
            await self.send_message(context, "⏳ _Processing your request..._")
            
            # Use non-streaming response instead of streaming
            response = await mcp_client.process_query(
                messages_history, 
                self.store_new_messages if USE_PRODUCTION_DB else None
            )
            
            # Send the complete response
            if response:
                final_response = await self.send_message(context, response)
                return final_response
            else:
                return await self.send_message(context, "I couldn't generate a response. Please try again.")
                
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return await self.send_message(context, f"Error processing query: {str(e)}")

    async def process_query_stream(
            self,
            mcp_client: MCPClient,
            messages_history: List[ChatMessage],
            context: WhatsAppBotContext
    ) -> Any:
        """
        Process a query using streaming responses, but batching results for WhatsApp.
        This method handles streaming by collecting chunks and sending them in batches.

        Args:
            mcp_client: MCP client instance
            messages_history: List of previous messages
            context: WhatsApp bot context

        Returns:
            Final response message object
        """
        try:
            # Send initial waiting message
            await self.send_message(context, "⏳ _Processing your request..._")
            
            # Initialize variables to collect streaming chunks
            collected_chunks = ""
            current_chunk = ""
            special_messages = []
            buffer_size = 500  # Threshold for buffering text
            last_send_time = time.time()
            update_interval = 5.0  # Seconds between updates
            
            # Use MCP client's streaming generator
            async for chunk in mcp_client.process_query_stream(
                messages_history,
                self.store_new_messages if USE_PRODUCTION_DB else None
            ):
                # Check if this is a special message (like tool call)
                if chunk.startswith("<special>") and chunk.endswith("\n"):
                    # Extract the special message content
                    special_content = chunk.replace("<special>", "").split(mcp_client.get_message_split_token())[0].strip()
                    
                    # Send the current text chunk if we have any
                    if current_chunk:
                        collected_chunks += current_chunk
                        current_chunk = ""
                        if len(collected_chunks) >= buffer_size:
                            await self.send_message(context, collected_chunks)
                            collected_chunks = ""
                            last_send_time = time.time()
                    
                    # Send special message (like tool calls)
                    await self.send_special_message(context, special_content)
                    special_messages.append(special_content)
                    continue
                
                # Regular text chunk
                current_chunk += chunk
                
                # Check if it's time to send a buffer update
                current_time = time.time()
                should_send_update = (
                    (current_time - last_send_time >= update_interval and len(current_chunk) > 0) or
                    len(current_chunk) >= buffer_size
                )
                
                if should_send_update:
                    # Add chunk to collected text
                    collected_chunks += current_chunk
                    current_chunk = ""
                    
                    # Send intermediate update
                    await self.send_message(context, collected_chunks)
                    collected_chunks = ""
                    last_send_time = current_time
            
            # Send any remaining text
            final_text = collected_chunks + current_chunk
            if final_text:
                final_response = await self.send_message(context, final_text)
                return final_response
            else:
                # If no text was generated but we had special messages, send a summary
                if special_messages:
                    summary = "✅ *Task Completed*\n\n"
                    if any("Calling tool" in msg for msg in special_messages):
                        summary += "I've completed the requested operations using various tools."
                    return await self.send_message(context, summary)
                else:
                    return await self.send_message(context, "I couldn't generate a response. Please try again.")
                
        except Exception as e:
            logger.error(f"Error processing streaming query: {e}", exc_info=True)
            error_message = f"Error processing your request: {str(e)}"
            return await self.send_message(context, error_message)

    async def get_messages_history(
            self, conversation: Conversation, context: WhatsAppBotContext, limit: int = 6
    ) -> List[ChatMessage]:
        """
        Get the previous messages for the conversation.
        For WhatsApp, in local development mode, we just use the current message.
        
        Args:
            conversation: Conversation object
            context: WhatsApp bot context
            limit: Maximum number of previous messages to retrieve
            
        Returns:
            List of ChatMessage objects
        """
        if USE_PRODUCTION_DB:
            # In production, use the conversation history from the database
            # This would be implemented as needed, similar to SlackBot's implementation
            logger.info("Database operations for message history not implemented yet")
            
        # For local development, just use the current message
        logger.info("Using current message as history")
        return [
            ChatMessage(
                role=MessageRole.USER,
                content=[TextContent(text=f"User says: {context.user_message}")],
            )
        ]
        
    def run(self, port: Optional[int] = None) -> None:
        """
        Run the bot (placeholder - actual running is handled by FastAPI integration)
        
        Args:
            port: Optional port number (ignored for WhatsAppBot as it's handled by FastAPI)
        """
        logger.info(f"WhatsApp bot running within FastAPI server on port {port if port else 'default'}")
        pass

# Handle incoming WhatsApp messages
@wa.on_message()
async def handle_message(client: WhatsApp, message: Message):
    """Handle incoming WhatsApp messages"""
    logger.info(f"Received message: {message.text} from {message.from_user.wa_id}")
    
    try:
        # Use the message_id to mark as read and display typing indicator
        await client.indicate_typing(message_id=message.id)
        
        # Create WhatsApp bot instance
        whatsapp_bot = WhatsAppBot()
        
        # Create context for this message
        context = WhatsAppBotContext(
            platform_name="whatsapp",
            user_id=message.from_user.wa_id,
            message=message
        )
        
        # Get server URLs to connect to
        server_urls = await whatsapp_bot.get_server_urls(context)
        if not server_urls:
            await whatsapp_bot.send_message(
                context,
                "Sorry, I couldn't find any MCP servers to connect to. Please check your configuration."
            )
            return
            
        # Initialize MCP client
        mcp_client = await whatsapp_bot.initialize_mcp_client(context, server_urls)
        if not mcp_client:
            await whatsapp_bot.send_message(
                context,
                "Sorry, I couldn't initialize the MCP client. Please try again later."
            )
            return
            
        # Get conversation to get message history
        conversation = mcp_client.conversation
        
        # Get message history
        messages_history = await whatsapp_bot.get_messages_history(conversation, context)
        
        # Process the query with streaming
        await whatsapp_bot.process_query_stream(mcp_client, messages_history, context)
        
        # Cleanup MCP client resources
        await mcp_client.cleanup()
        
        logger.info(f"Processed message from {message.from_user.wa_id}")
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        # Try to send an error message
        try:
            await client.send_message(
                to=message.from_user.wa_id,
                text=f"Sorry, an error occurred: {str(e)}"
            )
        except:
            pass

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"status": "ok", "service": "WhatsApp Bot"}

# Add a webhook verification endpoint
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Manually handle webhook verification
    This helps to avoid issues with the automatic verification process
    """
    query_params = dict(request.query_params)
    
    # Extract verification parameters
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")
    
    # Verify parameters
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(content=challenge, media_type="text/plain")
    else:
        logger.error(f"Webhook verification failed. Mode: {mode}, Token: {token}")
        return Response(status_code=403)

# Add a webhook endpoint for receiving messages
@app.post("/webhook")
async def webhook(request: Request):
    """
    Handle incoming webhook events
    """
    body = await request.json()
    logger.debug(f"Received webhook: {body}")
    
    # Let the WhatsApp client process the webhook
    return await wa.process_webhook(body)

def main():
    """
    Main entry point for running the WhatsApp bot as a standalone service.
    """
    # Enable uvloop for better performance if available
    try:
        import uvloop
        uvloop.install()
        logger.info("Using uvloop for improved performance")
    except ImportError:
        logger.info("uvloop not available, using default event loop")
    
    # Run the FastAPI app
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting WhatsApp bot server on port {port}")
    logger.info(f"Using callback URL: {CALLBACK_URL}")
    
    # Using uvicorn directly
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()