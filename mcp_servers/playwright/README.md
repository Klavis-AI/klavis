


# Playwright MCP Server

An **MCP (Model Context Protocol)** server that provides browser automation capabilities via **Microsoft Playwright**.

This MCP server allows AI agents and tools to:
- Launch browsers
- Open pages
- Navigate to URLs
- Interact with elements
- Extract text
- Take screenshots

— all through a **unified MCP interface**.

---

## ✨ Features

The Playwright MCP server exposes the following **atomic tools**:

### **Browser Control**
- **`launch_browser`** – Start a browser instance (`chromium`, `firefox`, `webkit`)
- **`close_browser`** – Close a running browser

### **Page Management**
- **`new_page`** – Open a new tab/page in an existing browser
- **`close_page`** – Close a specific page/tab

### **Navigation & Interaction**
- **`go_to_url`** – Navigate a page to a given URL
- **`click_selector`** – Click an element using a CSS selector
- **`fill_selector`** – Fill a form input with text
- **`get_text`** – Extract inner text from an element

### **Media**
- **`take_screenshot`** – Capture a screenshot of the page

---

##  Setup

### **Prerequisites**
- Python **3.12** or higher
- Playwright installed
- Virtual environment (**recommended**)

---

## 📦 Installation

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install --with-deps
````

---

## 🚀 Running the Server

Run with **Uvicorn**:

```bash
uvicorn mcp_servers.playwright.server:app --host 0.0.0.0 --port 5050 --reload
```

**Expected startup log:**

```yaml
Playwright MCP server started; tools: click_selector, close_browser, close_page,
fill_selector, get_text, go_to_url, launch_browser, new_page, take_screenshot
```

---

## 🔌 MCP Endpoints

The server supports both **HTTP** and **SSE (Server-Sent Events)**:

| Endpoint  | Purpose                                 |
| --------- | --------------------------------------- |
| `/health` | Health check                            |
| `/tools`  | Lists all available tools               |
| `/mcp`    | Streamable HTTP endpoint for tool calls |
| `/sse`    | Server-Sent Events endpoint             |

---

##  Configuration

You can configure defaults via environment variables (`.env` file):

```ini
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_BROWSER=chromium
PORT=5050
```

---
## Tools (arguments • returns • common errors)

### launch_browser
**Args:** `browser_type: "chromium" | "firefox" | "webkit"` (optional), `headless: bool` (optional)  
**Returns:** `{ "browser_id": string, "browser_type": string, "headless": bool }`  
**Errors:** 400 if invalid `browser_type`.

### close_browser
**Args:** `browser_id: string`  
**Returns:** `{ "message": string }`  
**Errors:** 400 if browser not found.

### new_page
**Args:** `browser_id: string`  
**Returns:** `{ "page_id": string }`  
**Errors:** 400 if browser not found.

### close_page
**Args:** `page_id: string`  
**Returns:** `{ "message": string }`  
**Errors:** 400 if page not found.

### go_to_url
**Args:** `page_id: string`, `url: string`, `wait_until: string = "domcontentloaded"`, `timeout_ms: number = 60000`  
**Returns:** `{ "message": string }`  
**Errors:** 400 if page not found or `url` missing.

### click_selector
**Args:** `page_id: string`, `selector: string`, `timeout_ms: number = 30000`  
**Returns:** `{ "message": string }`  
**Errors:** 400 if page/selector not found.

### fill_selector
**Args:** `page_id: string`, `selector: string`, `text: string`, `timeout_ms: number = 30000`  
**Returns:** `{ "message": string }`  
**Errors:** 400 if page/selector not found.

### get_text
**Args:** `page_id: string`, `selector: string`, `timeout_ms: number = 30000`  
**Returns:** `{ "text": string }`  
**Errors:** 400 if page/selector not found.

### take_screenshot
**Args:** `page_id: string`, `full_page: bool = false`  
**Returns:** `{ "screenshot_base64": string }`  
**Errors:** 400 if page not found.

---

##  Tool Usage Examples

### **Launch Browser**

```json
{
  "name": "launch_browser",
  "arguments": {
    "browser_type": "chromium",
    "headless": true
  }
}
```

### **New Page**

```json
{
  "name": "new_page",
  "arguments": {
    "browser_id": "BROWSER_ID_FROM_LAUNCH"
  }
}
```

### **Go to URL**

```json
{
  "name": "go_to_url",
  "arguments": {
    "page_id": "PAGE_ID_FROM_NEW_PAGE",
    "url": "https://example.com"
  }
}
```

### **Get Text**

```json
{
  "name": "get_text",
  "arguments": {
    "page_id": "PAGE_ID_FROM_NEW_PAGE",
    "selector": "h1"
  }
}
```

### **Take Screenshot**

```json
{
  "name": "take_screenshot",
  "arguments": {
    "page_id": "PAGE_ID_FROM_NEW_PAGE",
    "path": "example.png"
  }
}
```

---

## 🧪 Testing the Server

### **1. Health Check**

```bash
curl -s http://localhost:5050/health
```

### **2. List Tools**

```bash
curl -s http://localhost:5050/tools
```

### **3. End-to-End Test (Example)**

```bash
# Launch Browser
curl -s -X POST localhost:5050/mcp -H "Content-Type: application/json" \
  -d '{"name":"launch_browser","arguments":{"browser_type":"chromium"}}'

# New Page → Go to Example.com → Get H1 → Screenshot → Close
```
---

##  Integrating with MCP Clients

### **Cursor**

Add to `mcpServers` in Cursor settings:

```json
{
  "mcpServers": {
    "PlaywrightMCP": {
      "url": "http://localhost:5050",
      "description": "Playwright MCP server (HTTP)"
    }
  }
}
```

### **Claude Desktop**

Add `mcp.json` pointing to:

```json
{
  "mcpServers": {
    "PlaywrightMCP": {
      "transport": "http",
      "url": "http://localhost:5050"
    }
  }
}
```

---

## Error Handling

The server returns **detailed error messages** for:

* Missing required parameters
* Invalid selectors
* Network/navigation errors
* Browser/page not found

---

##  Contributing

1. Follow the existing MCP server structure under `mcp_servers/`
2. Add new tools to the `tools/` directory
3. Update `__init__.py` to export new functions
4. Include NL prompts & proof screenshots for each tool

---

##  License

This project follows the same license as the **parent Klavis AI repository**.
