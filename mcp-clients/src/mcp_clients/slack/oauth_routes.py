import base64
import json
import logging
import urllib.parse
from typing import Optional, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from slack_sdk.web.async_client import AsyncWebClient

from mcp_clients.config import USE_PRODUCTION_DB
from mcp_clients.slack.settings import settings

if USE_PRODUCTION_DB:
    from mcp_clients.database.database import create_mcp_client, insert_slack_client_auth

# Configure logging
logger = logging.getLogger("slack_oauth")


class SlackOAuthResponse(BaseModel):
    """Model for Slack OAuth API response"""
    ok: bool
    app_id: Optional[str] = None
    authed_user: Optional[dict] = None
    team: Optional[dict] = None
    enterprise: Optional[dict] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    access_token: Optional[str] = None
    bot_user_id: Optional[str] = None
    error: Optional[str] = None


def setup_oauth_routes(router: APIRouter):
    """
    Set up OAuth routes for Slack app installation
    
    Args:
        router: FastAPI router to add routes to
    """

    @router.get("/slack/oauth/install")
    async def install_slack_app(account_id: str = None):
        """
        Redirect to Slack OAuth authorization page
        """
        if not settings.SLACK_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SLACK_CLIENT_ID environment variable is not set"
            )

        query_params = {
            "client_id": settings.SLACK_CLIENT_ID,
            "scope": settings.SLACK_SCOPES,
            "redirect_uri": settings.SLACK_REDIRECT_URI
        }

        state = None
        # Create state parameter with account_id if provided, this will be passed when user add Klavis powered Slack MCP Client
        if account_id:
            logger.info(f"Installing Klavis powered Slack MCP Client with account_id: {account_id}")
            state_data = {"account_id": account_id}
            state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        if state:
            query_params["state"] = state

        encoded_params = urllib.parse.urlencode(query_params)

        auth_url = f"https://slack.com/oauth/v2/authorize?{encoded_params}"

        logger.info(f"Redirecting to Slack OAuth: {auth_url}")
        return RedirectResponse(auth_url)

    @router.get("/slack/oauth/callback")
    async def oauth_callback(code: str = None, error: str = None, state: str = None):
        """
        Handle OAuth callback from Slack
        
        Args:
            code: Authorization code from Slack
            error: Error message from Slack
            state: State parameter passed during authorization
        """
        if error:
            logger.error(f"OAuth error: {error}")
            return {"error": error}

        if not code:
            logger.error("No authorization code received")
            return {"error": "No authorization code received"}

        # Extract account_id from state parameter if it exists
        account_id = None
        if state:
            try:
                state_data = json.loads(base64.urlsafe_b64decode(state).decode())
                account_id = state_data.get("account_id")
                if account_id:
                    logger.info(f"OAuth callback received with account_id: {account_id} (from state)")
            except Exception as e:
                logger.error(f"Error decoding state parameter: {str(e)}")

        oauth_response = await exchange_code_for_token(code)

        if not oauth_response.ok:
            logger.error(f"OAuth token exchange failed: {oauth_response.error}")
            return {"error": oauth_response.error or "OAuth token exchange failed"}

        logger.info(f"Successfully authenticated for team: {oauth_response.team}")

        if not oauth_response.team or not oauth_response.team.get("id"):
            logger.error("Team ID not found in OAuth response")
            return {"error": "Team ID not found in OAuth response"}

        # Get user profile to obtain username
        user_id = oauth_response.authed_user.get("id") if oauth_response.authed_user else None
        username = None

        if user_id:
            username, _ = await get_user_profile(
                user_id=user_id,
                bot_token=oauth_response.access_token
            )

        mcp_client_result = {"mcp_client": None}

        if account_id and USE_PRODUCTION_DB:
            # Create Slack MCP Client with auth metadata
            mcp_client_result = await create_mcp_client(
                account_id=account_id,
                mcp_client_name=oauth_response.team.get("name"),
                external_id=oauth_response.team.get("id"),
                external_user_id=oauth_response.authed_user.get("id"),
                external_username=username,
                platform="slack",
            )

            if mcp_client_result["error"]:
                error_msg = f"Failed to create MCP client for account {account_id}"
                logger.error(error_msg)
                return {"error": error_msg}

            # Save auth metadata to `slack_client_auth` table
            auth_result = await insert_slack_client_auth(
                team_id=oauth_response.team.get("id"),
                auth_metadata=oauth_response.model_dump()
            )

            if auth_result["error"]:
                logger.error(f"Failed to save Slack auth metadata: {auth_result['error']}")
                # do not return, continue

        # Send welcome message
        try:
            user_id = oauth_response.authed_user.get("id") if oauth_response.authed_user else None
            if user_id:
                success, error_message = await send_welcome_message(
                    user_id=user_id,
                    username=username,
                    bot_token=oauth_response.access_token,
                    mcp_client_result=mcp_client_result
                )
                if not success:
                    logger.error(f"Error sending welcome message: {error_message}")
            else:
                logger.warning("Could not identify installing user to send welcome message")
        except Exception as e:
            logger.error(f"Error sending welcome message: {str(e)}")

        if account_id and mcp_client_result["mcp_client"] and mcp_client_result["mcp_client"].get("id"):
            # Redirect to client-specific page
            redirect_url = f"{settings.WEBSITE_URL}/home/mcp-client/{mcp_client_result['mcp_client'].get('id')}"
            return RedirectResponse(url=redirect_url)
        else:
            # Fall back to generic success page if client ID not available
            return RedirectResponse(url="/slack/oauth/success")

    async def exchange_code_for_token(code: str) -> SlackOAuthResponse:
        token_url = "https://slack.com/api/oauth.v2.access"

        # Prepare data for token exchange using urllib.parse
        data = {
            "client_id": settings.SLACK_CLIENT_ID,
            "client_secret": settings.SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.SLACK_REDIRECT_URI
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        data = response.json()
        return SlackOAuthResponse(**data)

    async def get_user_profile(user_id: str, bot_token: str) -> tuple[str, dict]:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://slack.com/api/users.info",
                headers={"Authorization": f"Bearer {bot_token}"},
                params={"user": user_id}
            )

        user_data = user_response.json()
        username = "slack_user"  # Default username

        if user_data.get("ok") and user_data.get("user"):
            user_info = user_data.get("user", {})
            profile = user_info.get("profile", {})

            # Try to get the best available username option
            if profile.get("display_name"):
                username = profile.get("display_name")
            elif profile.get("real_name"):
                username = profile.get("real_name")
            elif user_info.get("name"):
                username = user_info.get("name")

            # Remove spaces for URL safety
            username = username.replace(" ", "_")

        return username, user_data


async def send_welcome_message(user_id: str, username: str, bot_token: str, mcp_client_result: Dict[str, Any]):
    """
    Send a welcome message to a Slack user.
    
    Args:
        user_id: Slack user ID
        username: Slack username
        bot_token: Slack bot token
        mcp_client_result: Dictionary containing client information
    """
    try:
        client_id = mcp_client_result.get("mcp_client", {}).get("id", "")
        if not client_id:
            dashboard_url = f"{settings.WEBSITE_URL}/home"
        else:
            dashboard_url = f"{settings.WEBSITE_URL}/home/mcp-client/{client_id}"
        welcome_blocks = create_welcome_blocks(dashboard_url)

        client = AsyncWebClient(token=bot_token)
        response = await client.chat_postMessage(
            channel=user_id,
            text="Thanks for installing our app! 🎉",
            blocks=welcome_blocks
        )

        if response["ok"]:
            return True, None
        else:
            error_message = response.get("error", "Unknown error")
            return False, error_message
    except Exception as e:
        return False, str(e)


def create_welcome_blocks(dashboard_url: str):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🎉 Welcome to Klavis AI*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Thanks for installing our Slack bot. You're all set to use AI-powered assistance right from Slack."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Connect to an MCP server to get started, then simply mention the Klavis AI bot in a channel or send a direct message."
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Connect to MCP server",
                        "emoji": True
                    },
                    "action_id": "connect_mcp_server_button",
                    "url": dashboard_url,
                    "style": "primary"
                }
            ]
        }
    ]
