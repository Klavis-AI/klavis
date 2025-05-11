# Klavis AI WhatsApp Bot

This is the WhatsApp integration for the Klavis AI system, allowing users to interact with Klavis AI through WhatsApp messages.

## Features

- Asynchronous message handling with FastAPI
- Support for WhatsApp Business Cloud API
- Streaming responses with batched delivery for better UX
- Integration with MCP servers for extended functionality
- Auto-splitting of long messages to fit WhatsApp limits
- Special handling for tool calls and running operations

## Setup Requirements

- WhatsApp Business API access (via Meta Developer Account)
- Python 3.12+
- Environment variables for WhatsApp API credentials

## Environment Variables

```
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_verification_token
WHATSAPP_APP_ID=your_app_id
WHATSAPP_APP_SECRET=your_app_secret
CALLBACK_URL=your_webhook_url
PORT=8080
```

## WhatsApp API Setup

1. Create a Meta Developer account at [developers.facebook.com](https://developers.facebook.com/)
2. Create a new "Business" type app and add the WhatsApp product
3. Configure webhook subscriptions for `messages` and `message_reactions`
4. Set your verification token (must match `WHATSAPP_VERIFY_TOKEN`)
5. Get your test phone number or link a WhatsApp Business account

## Local Development

```bash
# Install dependencies
uv sync

# Run the bot
python -m src.mcp_clients.whatsapp_bot
```

## Using Docker

```bash
# Build the Docker image
docker build -t klavis-whatsapp-bot -f Dockerfile.whatsapp .

# Run with environment variables
docker run -p 8080:8080 --env-file .env klavis-whatsapp-bot
```

## Exposing Local Development for Testing

Use ngrok or similar tools to expose your local server:

```bash
ngrok http 8080
```

Update the webhook URL in the Meta Developer Dashboard and the `CALLBACK_URL` environment variable with the ngrok URL.

## Important WhatsApp API Considerations

- Must use template messages for initial outbound messages
- 24-hour messaging window restriction after user contact
- Message templates require approval by Meta
- Rate limits apply (see [WhatsApp Business API documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/))

## Troubleshooting

- Check webhook verification configuration
- Verify access token hasn't expired
- Use template messages when initiating conversation
- Check bot logs for detailed error information

## Architecture

The WhatsApp bot is built on FastAPI and uses the pywa_async library for WhatsApp interactions. It connects to MCP servers to provide AI functionality and tool capabilities to users through WhatsApp.