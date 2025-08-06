import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Mock registry of tools
TOOLS = {}

def register_tool(name, func):
    TOOLS[name] = func

@app.route('/tools', methods=['GET'])
def list_tools():
    return jsonify(list(TOOLS.keys()))

@app.route('/run/<tool_name>', methods=['POST'])
def run_tool(tool_name):
    if tool_name not in TOOLS:
        return jsonify({'error': 'Tool not found'}), 404
    data = request.get_json()
    try:
        result = TOOLS[tool_name](**data)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from tools import list_projects, create_project, list_databases, create_database, list_users, list_orders, run_sql
    register_tool("list_projects", list_projects.run)
    register_tool("create_project", create_project.run)
    register_tool("list_databases", list_databases.run)
    register_tool("create_database", create_database.run)
    register_tool("list_users", list_users.run)
    register_tool("list_orders", list_orders.run)
    register_tool("run_sql", run_sql.run)
    app.run(host='0.0.0.0', port=5000)
