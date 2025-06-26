# CrewAI + Klavis Multi-Service Research Crew

This example demonstrates how to use CrewAI with Klavis MCP servers to create a multi-service AI crew that can research YouTube videos and send email summaries.

## Features

- **YouTube Content Analysis**: Analyzes YouTube videos and extracts transcripts with timestamps
- **Email Communication**: Sends professional email summaries based on research findings
- **Multi-Agent Workflow**: Coordinates between specialized agents for different tasks

## Prerequisites

- Python 3.8+
- OpenAI API key
- Klavis API key

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your_openai_api_key"
export KLAVIS_API_KEY="your_klavis_api_key"
```

## Usage

1. Edit the configuration in `multi_service_crew.py`:
   - Change `VIDEO_URL` to your desired YouTube video
   - Update `RECIPIENT_EMAIL` to your email address

2. Run the script:
```bash
python multi_service_crew.py
```

3. Follow the OAuth authorization flow for Gmail when prompted

## How it Works

1. **YouTube MCP Server**: Creates a server instance for YouTube video analysis
2. **Gmail MCP Server**: Creates a server instance for sending emails (requires OAuth)
3. **Research Agent**: Analyzes the YouTube video and extracts key insights
4. **Email Agent**: Drafts and sends a professional email with the research findings
5. **Sequential Workflow**: The email task waits for the research task to complete

## Configuration

The script uses two main configuration variables:
- `VIDEO_URL`: The YouTube video to analyze
- `RECIPIENT_EMAIL`: The email address to send results to

## Security

- Never commit API keys to version control
- Use environment variables for sensitive configuration
- The Gmail integration requires OAuth authentication for security

## Troubleshooting

- Ensure both API keys are set as environment variables
- Complete the Gmail OAuth flow before proceeding
- Check that MCP servers are accessible and running
- Review verbose output by setting `verbose=True` in the Crew configuration 