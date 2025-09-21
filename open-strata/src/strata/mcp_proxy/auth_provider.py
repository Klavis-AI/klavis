import threading
import time
import webbrowser
import os
import json
import logging

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken


# Set up logging
logger = logging.getLogger(__name__)

TOKEN_DIRECTORY = '.tokens'

class LocalTokenStorage(TokenStorage):
    """Simple in-memory token storage implementation."""

    def __init__(self, server_name: str = "default"):
        self.server_name: str = server_name
        self._tokens: OAuthToken | None = None
        self._client_info: OAuthClientInformationFull | None = None
        self.token_lock = threading.Lock()
        self.info_lock = threading.Lock()
        self.TOKEN_PATH = os.path.join(TOKEN_DIRECTORY, self.server_name,"tokens.json")

    async def get_tokens(self) -> OAuthToken | None:
        if os.path.exists(self.TOKEN_PATH) and self._tokens is None:
            with self.token_lock:
                with open(self.TOKEN_PATH, "r") as f:
                    try:
                        data = json.load(f)
                        self._tokens = OAuthToken.model_validate(data)
                    except Exception as e:
                        logger.info("Error loading tokens:", e)
        return self._tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens
        os.makedirs(os.path.dirname(self.TOKEN_PATH), exist_ok=True)
        with self.token_lock:
            with open(self.TOKEN_PATH, "w") as f:
                dump = tokens.model_dump(exclude_none=True, mode='json')
                json.dump(dump, f)

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._client_info = client_info


class CallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler to capture OAuth callback."""

    def __init__(self, request, client_address, server, callback_data):
        """Initialize with callback data storage."""
        self.callback_data = callback_data
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)

        if "code" in query_params:
            self.callback_data["authorization_code"] = query_params["code"][0]
            self.callback_data["state"] = query_params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </body>
            </html>
            """)
        elif "error" in query_params:
            self.callback_data["error"] = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
            <html>
            <body>
                <h1>Authorization Failed</h1>
                <p>Error: {query_params["error"][0]}</p>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """.encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class CallbackServer:
    """Simple server to handle OAuth callbacks."""

    def __init__(self, port=3000):
        self.port = port
        self.server = None
        self.thread = None
        self.callback_data = {"authorization_code": None, "state": None, "error": None}

    def _create_handler_with_data(self):
        """Create a handler class with access to callback data."""
        callback_data = self.callback_data

        class DataCallbackHandler(CallbackHandler):
            def __init__(self, request, client_address, server):
                super().__init__(request, client_address, server, callback_data)

        return DataCallbackHandler

    def start(self):
        """Start the callback server in a background thread."""
        handler_class = self._create_handler_with_data()
        self.server = HTTPServer(("localhost", self.port), handler_class)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"🖥️  Started callback server on http://localhost:{self.port}")

    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)

    def wait_for_callback(self, timeout=300):
        """Wait for OAuth callback with timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.callback_data["authorization_code"]:
                return self.callback_data["authorization_code"]
            elif self.callback_data["error"]:
                raise Exception(f"OAuth error: {self.callback_data['error']}")
            time.sleep(0.1)
        raise Exception("Timeout waiting for OAuth callback")

    def get_state(self):
        """Get the received state parameter."""
        return self.callback_data["state"]
    
def create_oauth_provider(server_name: str, url: str) -> OAuthClientProvider:
    """Create OAuth authentication provider."""
    client_metadata_dict = {
        "client_name": "KLAVIS Strata MCP Router",
        "redirect_uris": ["http://localhost:3030/callback"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post",
    }

    async def callback_handler() -> tuple[str, str | None]:
        """Wait for OAuth callback and return auth code and state."""
        callback_server = CallbackServer(port=3030)
        callback_server.start()
        logger.info("⏳ Waiting for authorization callback...")
        try:
            auth_code = callback_server.wait_for_callback(timeout=300)
            return auth_code, callback_server.get_state()
        finally:
            callback_server.stop()

    async def _default_redirect_handler(authorization_url: str) -> None:
        """Default redirect handler that opens the URL in a browser."""
        logger.info(f"Opening browser for authorization: {authorization_url}")
        webbrowser.open(authorization_url)

    auth_url = ""
    if url.endswith("/mcp"):
        auth_url = url[:-4]
    elif url.endswith("/sse"):
        auth_url = url[:-4]
    else:
        auth_url = url
    
    return OAuthClientProvider(
        server_url=auth_url,
        client_metadata=OAuthClientMetadata.model_validate(client_metadata_dict),
        storage=LocalTokenStorage(server_name),
        redirect_handler=_default_redirect_handler,
        callback_handler=callback_handler,
    )