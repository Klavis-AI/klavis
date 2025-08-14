#!/usr/bin/env python3
"""
Web Bridge for Exa MCP Server
Connects the beautiful HTML UI to your real MCP tools
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)
CORS(app)

# Global variables
mcp_initialized = False
tools_registry = None
server_instance = None

async def initialize_mcp_server():
    """Initialize the MCP server once"""
    global mcp_initialized, tools_registry, server_instance
    
    if not mcp_initialized:
        try:
            # Import the main module
            from src.main import initialize_server
            
            # Try to get tools_registry if it exists
            try:
                from src.main import tools_registry as tr
                tools_registry = tr
            except ImportError:
                print("⚠️  tools_registry not found in main.py, will use fallback")
                tools_registry = {}
            
            # Initialize the server
            server_result = await initialize_server()
            server_instance = server_result
            
            # If tools_registry is still empty, try to populate it manually
            if not tools_registry:
                tools_registry = {
                    "search_web": "AI Web Search",
                    "find_similar_content": "Find Similar Content", 
                    "search_recent_content": "Recent Content Search",
                    "search_academic_content": "Academic Search",
                    "get_page_contents": "Extract Content"
                }
                print("🔧 Using fallback tools registry")
            
            mcp_initialized = True
            print(f"✅ MCP Server initialized successfully with {len(tools_registry)} tools")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize MCP server: {e}")
            print(f"Error details: {type(e).__name__}: {str(e)}")
            # Still set some basic tools so the UI works
            tools_registry = {
                "search_web": "AI Web Search",
                "find_similar_content": "Find Similar Content", 
                "search_recent_content": "Recent Content Search",
                "search_academic_content": "Academic Search",
                "get_page_contents": "Extract Content"
            }
            return False
    return True

@app.route('/')
def serve_ui():
    """Serve the main HTML UI"""
    return send_from_directory('.', 'demo.html')

@app.route('/api/status')
def get_status():
    """Check server status"""
    # Ensure we have tools_registry populated
    if tools_registry is None:
        available_tools = []
    else:
        available_tools = list(tools_registry.keys())
    
    return jsonify({
        "status": "connected" if mcp_initialized else "disconnected",
        "tools_available": available_tools,
        "tools_count": len(available_tools),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/execute', methods=['POST'])
def execute_tool():
    """Execute a tool with real API calls"""
    try:
        data = request.json
        tool_name = data.get('tool')
        query = data.get('query', '')
        
        print(f"🔧 Received execute request: tool={tool_name}, query='{query[:50]}...'")
        
        # Validate inputs
        if not tool_name:
            return jsonify({"success": False, "error": "Tool name is required"})
        
        if not query and tool_name not in ['find_similar_content', 'get_page_contents']:
            return jsonify({"success": False, "error": "Query is required"})
        
        # Prepare arguments based on tool
        if tool_name == 'search_web':
            args = {
                "query": query,
                "num_results": data.get('num_results', 5),
                "type": data.get('search_type', 'neural')
            }
        elif tool_name == 'find_similar_content':
            # For similarity, query should be a URL
            # Validate URL format and provide helpful error if not valid
            if not query.startswith(('http://', 'https://')):
                return jsonify({
                    "success": False, 
                    "error": f"Find Similar Content requires a valid URL starting with http:// or https://. You entered: '{query}'. Example: https://openai.com/blog/gpt-4"
                })
            args = {
                "url": query,
                "num_results": data.get('num_results', 5)
            }
        elif tool_name == 'search_recent_content':
            args = {
                "query": query,
                "days_back": data.get('days_back', 7),
                "num_results": data.get('num_results', 5)
            }
        elif tool_name == 'search_academic_content':
            args = {
                "query": query,
                "num_results": data.get('num_results', 5)
            }
        elif tool_name == 'get_page_contents':
            # Query should be result IDs (comma-separated)
            ids = [id.strip() for id in query.split(',') if id.strip()]
            args = {
                "ids": ids,
                "text": True,
                "summary": data.get('summary', True),
                "highlights": data.get('highlights', True)
            }
        else:
            return jsonify({"success": False, "error": f"Unknown tool: {tool_name}"})
        
        print(f"📤 Executing with args: {args}")
        
        # Execute the tool asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(execute_tool_async(tool_name, args))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Execute error: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Execution failed: {str(e)}"
        })

async def execute_tool_async(tool_name, args):
    """Execute tool asynchronously"""
    try:
        # Ensure MCP server is initialized
        if not await initialize_mcp_server():
            return {"success": False, "error": "MCP server initialization failed"}
        
        # Import and call the tool
        try:
            from src.main import call_tool
            print(f"🔧 Calling tool: {tool_name}")
            result = await call_tool(tool_name, args)
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return {"success": False, "error": f"Could not import call_tool: {str(e)}"}
        
        if result and len(result) > 0:
            response_text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            print(f"✅ Tool executed successfully, response length: {len(response_text)}")
            
            return {
                "success": True,
                "tool": tool_name,
                "query": args.get('query', args.get('url', args.get('ids', 'N/A'))),
                "result": response_text,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "No result returned from tool"}
            
    except Exception as e:
        print(f"❌ Tool execution error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return {"success": False, "error": str(e)}

@app.route('/api/tools')
def list_tools():
    """List available tools"""
    tools = [
        {
            "name": "search_web",
            "title": "🔍 AI Web Search",
            "description": "Neural semantic search that understands context and meaning"
        },
        {
            "name": "find_similar_content", 
            "title": "🔗 Find Similar Content",
            "description": "Discover semantically similar pages using AI embeddings"
        },
        {
            "name": "search_recent_content",
            "title": "📅 Recent Content Search", 
            "description": "Time-filtered search for fresh, up-to-date information"
        },
        {
            "name": "search_academic_content",
            "title": "🎓 Academic Search",
            "description": "Scholarly articles and research papers from academic sources"
        },
        {
            "name": "get_page_contents",
            "title": "📄 Extract Content",
            "description": "Full text extraction with AI summaries and highlights"
        }
    ]
    
    return jsonify({"tools": tools})

@app.route('/api/debug')
def debug_info():
    """Debug endpoint to check what's loaded"""
    return jsonify({
        "mcp_initialized": mcp_initialized,
        "tools_registry": tools_registry,
        "tools_count": len(tools_registry) if tools_registry else 0,
        "server_instance": str(type(server_instance)) if server_instance else None,
        "sys_path": sys.path[:3]  # First 3 entries
    })

if __name__ == '__main__':
    print("🚀 Starting Exa MCP Web Bridge...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🎬 Open demo.html in your browser to start recording!")
    print("🐛 Debug info available at: http://localhost:8000/api/debug")
    print()
    
    # Initialize MCP server in the main thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        init_success = loop.run_until_complete(initialize_mcp_server())
        if init_success:
            print(f"✅ MCP Server ready for web requests with {len(tools_registry)} tools")
        else:
            print("⚠️  MCP Server initialization had issues, but web server will still start")
            print(f"📋 Available tools: {list(tools_registry.keys()) if tools_registry else 'None'}")
    except Exception as e:
        print(f"⚠️  MCP initialization error: {e}")
    finally:
        loop.close()
    
    # Start Flask web server
    app.run(host='localhost', port=8000, debug=True)