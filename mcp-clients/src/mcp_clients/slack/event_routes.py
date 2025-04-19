import logging
from typing import Callable

import time
from fastapi import Request, Response
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("slack_bot")


def setup_http_routes(router, slack_handler: AsyncSlackRequestHandler):
    """
    Set up HTTP routes for Slack app integration
    
    Args:
        router: FastAPI router to add routes to
        slack_handler: Slack request handler for processing events
    """
    route_logger = logging.getLogger("slack_bot.routes")

    @router.post("/slack/events")
    async def slack_events_post(request: Request):
        """Endpoint for Slack events (POST method)"""
        route_logger.info("--- Received Slack event (POST)")

        # Get the JSON body
        body = await request.json()

        # Handle URL verification challenge
        if body.get("type") == "url_verification":
            route_logger.info("Handling Slack URL verification challenge")
            challenge = body.get("challenge")
            if challenge:
                route_logger.info(f"Responding with challenge: {challenge}")
                return {"challenge": challenge}

        # Filter out bot messages early
        if body.get("event") and body.get("event").get("bot_id"):
            route_logger.debug("--- Ignoring bot message")
            return {"ok": True}  # Return 200 OK to acknowledge 

        response = await slack_handler.handle(request)
        return response

    @router.post("/slack/interactive")
    async def slack_interactive(request: Request):
        """Endpoint for Slack interactive components (buttons, modals, etc.)"""
        route_logger.info("---Received Slack interactive component request")
        return await slack_handler.handle(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get request details
        path = request.url.path
        method = request.method

        # Log request
        logger.info(f"Request: {method} {path}")

        # Process the request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            status_code = response.status_code
            logger.info(f"Response: {method} {path} - Status: {status_code} - Time: {process_time:.3f}s")

            return response
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(f"Error: {method} {path} - Error: {str(e)} - Time: {process_time:.3f}s")
            raise
