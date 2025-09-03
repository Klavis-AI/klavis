# Google Photos MCP Server Setup

## 1. Create a Google Cloud Project & OAuth App

- Go to [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project (or select an existing one).
- Enable the **Google Photos Library API** and **Google Photos Picker API** for your project.
- Go to **APIs & Services > Credentials**.
- Click **Create Credentials > OAuth client ID**.
- Choose **Desktop app** or **Web application** (as needed).
- Download the OAuth credentials and save the file as `credentials.json` in your google_photos folder.

## 2. Generate OAuth Token

- Use the provided `get_photos_token.py` script or your own method to generate an access token and refresh token.
- Save the access token and refresh token in your `.env` file or directly in your `mcp.json` (see below).


## 3. Set Up Your `.env` File

Create a `.env` file in `mcp_servers/google_photos/` with:
```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REFRESH_TOKEN=your-refresh-token
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_PHOTOS_MCP_SERVER_PORT=5000
```

## 4. Configure `mcp.json` for Natural Language Agents

To interact with your MCP server using agents like Copilot, Cursor, etc., set up `.vscode/mcp.json` in your repo root:
```jsonc
{
    "servers": {
        "google_photos": {
            "type": "http",
            "url": "http://localhost:5000/mcp",
            "headers": {
                "x-api-token": "YOUR_ACCESS_TOKEN",
                "x-token-uri": "https://oauth2.googleapis.com/token",
                "x-refresh-token": "YOUR_REFRESH_TOKEN"
            }
        }
    }
}
```


## 5. Run the Server (Docker or Bare Metal)

You can run the Google Photos MCP server either with Docker or directly (bare metal):

### Option 1: Docker (Recommended)
From the root of your repo (`/workspaces/klavis`), build and run the server:

```bash
docker build -f mcp_servers/google_photos/Dockerfile -t my-google-photos-server .
docker run --env-file mcp_servers/google_photos/.env -p 5000:5000 my-google-photos-server
```

### Option 2: Bare Metal (Directly on Host)
From the `mcp_servers/google_photos` directory, install requirements and run:

```bash
pip install -r requirements.txt
python server.py
```

Your Google Photos MCP server will be running and accessible at http://localhost:5000. You can now interact with it using natural language agents!

@Priyanshuthapliyal2005