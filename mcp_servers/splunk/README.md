# Splunk MCP Server

Model Context Protocol (MCP) server for Klavis AI — exposes atomic Splunk tools for AI workflows.

---

## Setup

### 1. **Clone and enter folder:**
```sh
git clone https://github.com/Klavis-AI/klavis.git
cd klavis/mcp_servers/splunk
```

### 2. **Set up Splunk**

**A. Local Install:**
- [Download Splunk Enterprise](https://www.splunk.com/en_us/download/splunk-enterprise.html) and install (default ports: 8000 for Web UI, 8089 for REST API).
- Start Splunk:
  ```sh
  cd /Applications/Splunk/bin   # (or your Splunk install location)
  ./splunk start
  ```
- Access the Splunk Web UI at: [http://localhost:8000](http://localhost:8000)

**B. Splunk Cloud:**
- [Sign up for Splunk Cloud](https://www.splunk.com/en_us/cloud.html) and get your cloud instance URL.
- Note your REST API endpoint and credentials.
- Use your Splunk Cloud URL for `SPLUNK_HOST` and ensure port `8089` or your cloud REST API port.

---

### 3. **Create `.env`:**
```ini
SPLUNK_HOST=host.docker.internal      # or your cloud host/IP
SPLUNK_PORT=8089
SPLUNK_USERNAME=your_splunk_username
SPLUNK_PASSWORD=your_splunk_password
```

---

### 4. **Build Docker image:**
```sh
docker build -t klavis-splunk .
```

---

### 5. **Run the server:**
```sh
docker run --env-file .env -p 8001:8001 klavis-splunk
```
Swagger UI: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Usage

- **Search logs** (`/search_logs`):
   ```json
   {
     "query": "search index=_internal | head 1",
     "earliest_time": "0",
     "latest_time": "now"
   }
   ```
- **Get events** (`/get_events`):  
   index: `_internal`  
   limit: `5`
- **Trigger alert** (`/trigger_alert`):
   ```json
   {
     "alert_name": "Test Alert",
     "params": {}
   }
   ```

---

## Testing

```sh
docker run --env-file .env -it klavis-splunk pytest
```

---

## Troubleshooting

- Use `localhost` for Splunk host if local
- Ensure Splunk REST API (`8089`) is running
- Check `.env` credentials

---

MIT License.
