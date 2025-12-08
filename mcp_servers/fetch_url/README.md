# MCP NPX Fetch

A HTTP transportation version of https://github.com/tokenizin-agency/mcp-npx-fetch. It's a MCP server that will fetch url and covert to the following format: HTLM, Text, Markdown, JSON

## 💻 Local Development

1. Install dependencies:

```bash
npm install
```

2. Start local deployment

```bash
npm rum build
npm start
```

3. Get MCP http URL

The MCP should be hosted at `http://localhost:8000/mcp`.

## 🐳 Docker Deployment

1. Build the Docker image (from the repository root):

```bash
docker build -f mcp_servers/fetch_url/Dockerfile -t fetch-url-mcp .
```

2. Run the container:

```bash
docker run -p 8000:8000 fetch-url-mcp
```

3. Access the MCP server at `http://localhost:8000/mcp`


## 📚 Documentation

### Available Tools

#### `fetch_html`

Fetches and returns raw HTML content from any URL.

```typescript
{
  url: string;     // Required: Target URL
  headers?: {      // Optional: Custom request headers
    [key: string]: string;
  };
}
```

#### `fetch_json`

Fetches and parses JSON data from any URL.

```typescript
{
  url: string;     // Required: Target URL
  headers?: {      // Optional: Custom request headers
    [key: string]: string;
  };
}
```

#### `fetch_txt`

Fetches and returns clean plain text content, removing HTML tags and scripts.

```typescript
{
  url: string;     // Required: Target URL
  headers?: {      // Optional: Custom request headers
    [key: string]: string;
  };
}
```

#### `fetch_markdown`

Fetches content and converts it to well-formatted Markdown.

```typescript
{
  url: string;     // Required: Target URL
  headers?: {      // Optional: Custom request headers
    [key: string]: string;
  };
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.