# Klavis Google Slides MCP Server, by Tazeem Mahashin

## Overview
This MCP server provides an interface to the Google Slides API through Klavis, allowing AI agents to create and manipulate Google Slides presentations. The server implements the Model Context Protocol (MCP) specification, making it compatible with various AI applications.

## Features
- Create new Google Slides presentations
- Add slides to existing presentations
- List available presentations
- Full MCP protocol compatibility with both SSE and StreamableHTTP transports

## Prerequisites
- Python 3.9 or higher
- Google Cloud Platform account with Google Slides API enabled
- Google API credentials (OAuth2 or Service Account)
- Docker (recommended for deployment)

## Setup & Configuration

### Google Cloud Setup
1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Slides API for your project
3. Set up authentication:
   - For service accounts: Create a service account, download the JSON key, and save it as `service-account.json` in the project directory
   - For OAuth: Create OAuth credentials, download the JSON file, and save it as `credentials.json` in the project directory

### Environment Configuration
1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your configuration:
   ```
   GOOGLE_SLIDES_MCP_SERVER_PORT=5000
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json  # Optional
   ```

## Running the Server

### Option 1: Docker (Recommended)
The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t google-slides-mcp-server -f mcp_servers/google_slides/Dockerfile .

# Run the container (with Google credentials mounted)
docker run -p 5000:5000 --rm \
  -v /path/to/credentials:/app/credentials.json \
  -v /path/to/service-account.json:/app/service-account.json \
  --env-file mcp_servers/google_slides/.env \
  google-slides-mcp-server
```

### Option 2: Python Virtual Environment
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Once running, the server will be accessible at `http://localhost:5000`

## MCP Tools
The server implements the Model Context Protocol (MCP) specification and provides the following tools:

### Available MCP Tools

#### create_presentation
Creates a new Google Slides presentation with the specified title.

```json
{
  "title": "My New Presentation"
}
```

#### add_slide
Adds a new slide to an existing presentation.

```json
{
  "presentation_id": "your_presentation_id",
  "title": "Slide Title",
  "content": "Slide Content"
}
```

#### list_presentations
Lists all available presentations in the user's Google Drive.

```json
{}
```

#### get_presentation
Retrieves detailed information about a specific presentation.

```json
{
  "presentation_id": "your_presentation_id",
  "fields": "presentationId,title,revisionId,slides,pageSize"
}
```

The `fields` parameter is optional and can be used to limit the returned data. If not provided, a default set of fields will be returned.

#### batch_update_presentation
Applies a series of updates to a presentation. This is the primary method for modifying slides (adding text, shapes, images, creating slides, etc.).

```json
{
  "presentation_id": "your_presentation_id",
  "requests": [
    {
      "createSlide": {
        "objectId": "MyNewSlide",
        "insertionIndex": 1,
        "slideLayoutReference": {
          "predefinedLayout": "TITLE_AND_BODY"
        }
      }
    },
    {
      "insertText": {
        "objectId": "MyNewSlide",
        "insertionIndex": 0,
        "text": "This is a slide title"
      }
    }
  ]
}
```

Refer to the [Google Slides API batchUpdate documentation](https://developers.google.com/slides/api/reference/rest/v1/presentations/batchUpdate) for details on request structure.

#### summarize_presentation
Extracts and formats all text content from a presentation for easier summarization.

```json
{
  "presentation_id": "your_presentation_id",
  "include_notes": false
}
```

The `include_notes` parameter is optional (defaults to false) and determines whether speaker notes should be included in the summary.

## Connection Methods

This MCP server supports two connection methods:

### SSE (Server-Sent Events)
```
GET http://localhost:5000/sse
```

### StreamableHTTP
```
POST http://localhost:5000/mcp
```

## Troubleshooting

### Authentication Issues
- Make sure your Google API credentials are correctly set up
- For service accounts, verify that the service account has the necessary permissions
- For OAuth, ensure the user has granted permission to access their Google Slides

### API Access Problems
- Check that the Google Slides API is enabled in your Google Cloud project
- Verify your credentials have not expired

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the same terms as the main Klavis project.
