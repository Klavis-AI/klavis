# YouTube MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that retrieves transcripts/subtitles for a given YouTube video and provides video details when transcripts are unavailable.

This server utilizes the `FastMCP` framework for handling MCP requests and the YouTube API.

## Features

*   Provides a simple MCP endpoint to get YouTube video transcripts.
*   Accepts a YouTube video URL as input.
*   Returns the transcript/subtitles when available.
*   Falls back to video details when transcript is unavailable.
*   Supports proxy configuration for transcript retrieval.
*   Built with Python using `FastMCP`.
*   Can be run easily using Docker or a standard Python environment.

## Environment Variables

The following environment variables are used by the server:

*   **Required**:
    *   `YOUTUBE_API_KEY`: Your YouTube Data API key (required for fetching video details).

*   **Optional**:
    *   `YOUTUBE_MCP_SERVER_PORT`: Port for the MCP server (defaults to 5000).
    *   `WEBSHARE_PROXY_USERNAME`: Username for Webshare proxy (optional, for circumventing regional restrictions).
    *   `WEBSHARE_PROXY_PASSWORD`: Password for Webshare proxy (optional, for circumventing regional restrictions).

For more information on using Webshare with YouTube Transcript API, refer to: [YouTube Transcript API - Using Webshare](https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#using-webshare)

## Running Locally

You can run this server locally using either Docker (recommended) or a Python virtual environment. The instructions assume you are in the root directory of the `klavis` project (the parent directory of `mcp_servers`).

### Prerequisites

*   **Docker:** If using the Docker method.
*   **Python:** Python 3.11+ if using the virtual environment method.
*   **`.env` File:** Create a file named `.env` in the root of the `klavis` project directory with the required environment variables.
    ```bash
    # Required
    YOUTUBE_API_KEY=your_youtube_api_key_here
    
    # Optional
    YOUTUBE_MCP_SERVER_PORT=5000
    WEBSHARE_PROXY_USERNAME=your_proxy_username
    WEBSHARE_PROXY_PASSWORD=your_proxy_password
    ```

### Using Docker (Recommended)

1.  **Build the Docker Image:**
    Open your terminal in the `mcp_servers/youtube` directory and run:
    ```bash
    docker build -t youtube-mcp-server .
    ```
    *   `-t youtube-mcp-server`: Assigns a tag (name) to the image.
    *   `.`: Specifies the build context (the current directory, `mcp_servers/youtube`).

2.  **Run the Docker Container:**
    ```bash
    docker run -p 5000:5000 --env-file .env youtube-mcp-server
    ```
    *   `-p 5000:5000`: Maps port 5000 on your host machine to port 5000 inside the container (where the server listens).
    *   `--env-file .env`: Provides the environment variables from your `.env` file to the container.
    *   `youtube-mcp-server`: The name of the image to run.

The server should now be running and accessible at `http://localhost:5000`.

### Using Python Virtual Environment

1.  **Navigate to Project Root:**
    Ensure your terminal is in the root directory of the `klavis` project.

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate Virtual Environment:**
    *   **Linux/macOS:** `source venv/bin/activate`
    *   **Windows:** `venv\Scripts\activate`

4.  **Install Dependencies:**
    The server relies on packages listed in `requirements.txt`:
    ```bash
    pip install -r mcp_servers/youtube/requirements.txt
    ```

5.  **Create `.env` File:**
    Ensure you have created the `.env` file in the `klavis` root directory as mentioned in the prerequisites.

6.  **Run the Server:**
    ```bash
    python mcp_servers/youtube/server.py
    ```

The server should now be running and accessible at `http://localhost:5000`.

## Usage

Once the server is running (either via Docker or Python environment), it listens for MCP requests on port 5000.

You can interact with it using an MCP client or tool. The available tool is:

* `get_youtube_video_transcript`:
  * **Description:** Retrieve the transcript/subtitles for a given YouTube video. When transcripts are unavailable, it will automatically fall back to fetching video details.
  * **Input Parameter:** `url` (string) - The URL of the YouTube video (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ).
  * **Returns:** (Dict) - Contains the transcript data when available, or video details with an error message when transcript is unavailable.
  * **Supported URL Formats:**
    * Standard: `youtube.com/watch?v=VIDEO_ID`
    * Short: `youtu.be/VIDEO_ID`
    * Embedded: `youtube.com/embed/VIDEO_ID`
    * Shorts: `youtube.com/shorts/VIDEO_ID`