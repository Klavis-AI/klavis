
"""
Simple script to create Klavis MCP server instance and redirect to OAuth authorization.
"""

import requests
import webbrowser
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('KLAVIS_API_KEY')

# Create MCP server instance
def create_mcp_instance(server_name, user_id, platform_name):
    url = "https://api.klavis.ai/mcp-server/instance/create"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "serverName": server_name,
        "userId": user_id,
        "platformName": platform_name
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    result = response.json()
    print(result)
    return result['instanceId']
        

# Redirect to OAuth authorization page
def redirect_to_oauth(instance_id):
    oauth_url = f"https://api.klavis.ai/oauth/github/authorize?instance_id={instance_id}"
    webbrowser.open(oauth_url)

def main():
    instance_id = create_mcp_instance("GitHub", "1234", "demo")
    redirect_to_oauth(instance_id)

if __name__ == "__main__":
    main() 