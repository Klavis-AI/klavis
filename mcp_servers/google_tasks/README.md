# Google Tasks MCP Server

The Google Tasks MCP Server is a Python-based server that exposes the functionality of the Google Tasks API through the Model Context Protocol (MCP). This allows AI agents to interact with Google Tasks in a structured and predictable way, enabling them to manage tasks and task lists on behalf of a user.

This server supports **Service Account** or **OAuth** authentication and is designed to be a robust and reliable component in an AI agent ecosystem.

---

## Features

* **List Task Lists** – Enumerate all task lists accessible to the account.
* **Create Task Lists** – Generate new lists to organize tasks.
* **List Tasks** – View all tasks within a specific list, with options to show or hide completed items.
* **Create Tasks** – Add new tasks with titles and optional notes to any list.
* **Update Tasks** – Modify existing tasks, including changing their title, notes, or status.
* **Mark Tasks as Complete** – A simple, dedicated tool for completing a task.

---

## Getting Started

### Prerequisites

* Python 3.8+
* A Google Cloud Platform (GCP) project.
* Access to the Google Tasks account you wish to manage.

---

### 1. Installation

First, set up a Python virtual environment:

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # On macOS/Linux
.venv\Scripts\activate      # On Windows

# Install required dependencies
pip install -r requirements.txt

  ```

### 2. Configuration

This server supports two authentication methods: Service Account and OAuth. Service Accounts are preferred for server-to-server communication.

  #### Step 1: Create a Service Account Key or OAuth credentials

1.  Go to the  [Google Cloud Console](https://console.cloud.google.com/)
2.  Enable the Google Tasks API for your project
3.  Set up authentication:
    -   Service accounts: Create a service account, download the JSON key, and save it as  `service-account.json`  in the project directory
    -   OAuth: Create OAuth credentials, download the JSON file, and save it as  `credentials.json`  in the project directory

  #### Step 2: **Create the `.env` file**

The `.env` file stores configuration settings so you don’t need to pass them manually each time.

Create a `.env` file in the project root with:

```
# .env configuration

# Port to run the MCP server on
PORT=8000

# Path to Service Account or OAuth credentials file
ENV_CREDENTIALS_PATH=service-account.json   # or credentials.json for OAuth

# Path to store OAuth token (if using OAuth)
ENV_TOKEN_PATH=token.json   # Optional

# Google API Scopes (default: full Google Tasks access)
ENV_SCOPES=https://www.googleapis.com/auth/tasks
```

### 3. Running the Server

Once credentials are configured:

  ```

# Start the server on the default port (8000)

python server.py

  ```