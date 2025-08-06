# Neon MCP Server

This is a Model Context Protocol (MCP) server for [Neon](https://neon.tech), allowing AI agents to interact with Neon via atomic tools.

## 🐳 One-Line Run Command
```bash
git clone <your-fork-url> && cd neon-mcp-server && docker-compose up --build
```

## ⚙️ Tools
- `list_projects()`
- `create_project(name)`
- `list_databases(project_id)`
- `create_database(project_id, name)`
- `list_users()`
- `list_orders()`
- `run_sql(project_id, sql_query)`

## 🧪 Sample Queries
- "List all my Neon projects."
- "Create a new Neon project called `AnalyticsPlatform`."
- "Show me all databases in my Neon project."
- "List all users."
- "Run a SQL query to find orders over $50."

## ✅ Proof of Correctness

### 📸 Screenshots
![List Projects](proof/list_projects.png)
![Create Project](proof/create_project.png)
![List Databases](proof/list_databases.png)
![Create Database](proof/create_database.png)
![Run SQL](proof/run_sql.png)

### 🎥 Demo
![Demo GIF](proof/demo.gif)

### 📊 How It Works
![How It Works](proof/how_it_works.png)

## 🔐 API Key
This demo uses a prefilled `.env.example` file. Replace with your own key for production.

