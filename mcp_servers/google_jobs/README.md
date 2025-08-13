# Google Jobs MCP Server

A MCP server that provides access to Google Jobs search functionality through SerpApi. This server enables AI assistants to search for job listings, get detailed job information, and perform specialized job searches.

## Features

- **Job Search**: Search for job listings with various filters (location, date, employment type, salary, etc.)
- **Job Details**: Get comprehensive information about specific job listings
- **Company Jobs**: Search for all job openings at specific companies
- **Remote Jobs**: Search specifically for remote job opportunities
- **Search Suggestions**: Get related job titles and search suggestions

## Prerequisites

- **SerpApi** account and API key
- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.8+ with pip

## SetUp & Configuration

1. Get a SerpApi API key:
   - Sign up at [SerpApi](https://serpapi.com/)
   - Get your API key from the dashboard
   - Add it to your `.env` file

2. Set up environment variables:
Create a `.env` file in the root directory:
```bash
SERPAPI_API_KEY=your_serpapi_api_key_here
GOOGLE_JOBS_MCP_SERVER_PORT=5000
```



## Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t google-jobs-mcp-server -f mcp_servers/google_jobs/Dockerfile .

# Run the container
docker run -d -p 5000:5000 --name google-jobs-mcp google-jobs-mcp-server
```

To use your local .env file instead of building it into the image:

```bash
docker run -d -p 5000:5000 --env-file mcp_servers/google_jobs/.env --name google-jobs-mcp google-jobs-mcp-server
```

### Option 2: Python Virtual Environment

```bash
# Navigate to the Google-Jobs server directory
cd mcp_servers/google_jobs

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Once running, the server will be accessible at `http://localhost:5000`.



## Project Structure

```
google-jobs-mcp-server/
├── .env                 # Environment variables (create this)
├── Dockerfile          # Docker configuration
├── README.md           # This file
├── server.py           # Main MCP server implementation
└── tools/              # Job search tools module
    ├── __init__.py     # Tool exports
    └── (additional tool files)
```


## Troubleshooting

**Common Issues:**

1. **"Error: query parameter is required"**: Ensure required parameters are provided in tool calls
2. **SerpApi authentication errors**: Verify your API key is correctly set
3. **Port conflicts**: Change the port using `--port` option or environment variable
4. **Import errors**: Ensure all dependencies are installed and the `tools` module is properly structured

**Getting Help:**

- Check the server logs for detailed error information
- Verify your SerpApi account has sufficient credits
- Ensure your API key has access to Google Jobs API

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Resources

- [SerpApi Google Jobs API Documentation](https://serpapi.com/google-jobs-api)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
