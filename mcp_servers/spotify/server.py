import os
import asyncio
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from tools.tool import register_all_tools

# ==== Load environment ==== 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==== Configuration ==== 
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
TOKEN = os.getenv("MCP_BEARER_TOKEN", "shadow-spotify-token")

# ==== Auth Provider ==== 
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(token=token, client_id="shadow-listener", scopes=[], expires_at=None)
        return None

# ==== Server Init ==== 
app = FastMCP("Spotify Music Explorer", auth=SimpleBearerAuthProvider(TOKEN))

# Register all tools
register_all_tools(app)

# ==== Run Server ==== 
async def main():
    print("🚀 Spotify Music Explorer MCP Server starting...")
    print(f"Using client ID: {SPOTIFY_CLIENT_ID}")
    print(f"Bearer token: {TOKEN}")
    print(f"Refresh token available: {'Yes' if SPOTIFY_REFRESH_TOKEN else 'No'}")
    
    # Validate Spotify credentials
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("⚠️ WARNING: Missing Spotify API credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file.")
    
    try:
        # Attempt to get an access token before starting the server
        from tools.spotify_api import SpotifyAPI
        print("Authenticating with Spotify...")
        await SpotifyAPI.ensure_token()
        print("✅ Spotify authentication successful!")
        
        await app.run_async("streamable-http", host="0.0.0.0", port=9090)
    except Exception as e:
        print(f"❌ Server error: {e}")
        print("Check your Spotify credentials and try again.")

if __name__ == "__main__":
    asyncio.run(main())