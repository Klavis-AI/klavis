import requests
import webbrowser
import os
import logging
import urllib.parse
from typing import Dict, Any, Optional, Literal
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

KLAVIS_API_BASE_URL = "https://api.klavis.ai"

# Type definitions for API enums
ServerName = Literal[
    "Markdown2doc", "Slack", "Supabase", "Postgres", "YouTube", "Doc2markdown", 
    "Klavis ReportGen", "Resend", "Discord", "Firecrawl Web Search", "GitHub", 
    "Firecrawl Deep Research", "Jira", "WordPress", "Notion", "Gmail", 
    "Google Drive", "Google Calendar", "Google Sheets", "Google Docs", 
    "Attio", "Salesforce", "Linear", "Asana", "Close"
]

OAUTH_SERVICE_NAME_TO_URL_PATH: Dict[ServerName, str] = {
  'Slack': 'slack',
  'Supabase': 'supabase',
  'GitHub': 'github',
  'Google Drive': 'gdrive',
  'Google Calendar': 'gcalendar',
  'Google Sheets': 'gsheets',
  'Google Docs': 'gdocs',
  'Jira': 'jira',
  'WordPress': 'wordpress',
  'Notion': 'notion',
  'Gmail': 'gmail',
  'Asana': 'asana',
  'Linear': 'linear',
  'Salesforce': 'salesforce',
  'Close': 'close',
  'Attio': 'attio',
}

ConnectionType = Literal["SSE", "StreamableHttp"]

class KlavisAPI:
    """Client for interacting with Klavis API."""
    def __init__(self, api_key: str, base_url: str = KLAVIS_API_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise RuntimeError(f"API request failed: {e}")
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}")
    
    def create_mcp_instance(self, server_name: ServerName, user_id: str, platform_name: str, 
                           connection_type: ConnectionType = "StreamableHttp") -> Dict[str, str]:
        """
        Create a dedicated MCP server instance for a user.
        
        Args:
            server_name: Name of the target MCP server (must be one of the supported servers)
            user_id: The identifier for the user requesting the server URL 
            platform_name: The name of the platform associated with the user 
            connection_type: The protocol to use for the MCP server (default: "StreamableHttp")
            
        Returns:
            Dictionary containing:
                - serverUrl: The full URL for connecting to the MCP server
                - instanceId: The unique identifier for this specific server connection instance
            
        Raises:
            ValueError: If input validation fails or response is invalid
            RuntimeError: If the API request fails
        """
        if not user_id or len(user_id.strip()) < 1:
            raise ValueError("userId must have minimum length of 1")
        
        if not platform_name or len(platform_name.strip()) < 1:
            raise ValueError("platformName must have minimum length of 1")
        
        data = {
            "serverName": server_name,
            "userId": user_id,
            "platformName": platform_name,
            "connectionType": connection_type
        }
        
        result = self._make_request("POST", "/mcp-server/instance/create", json=data)
        logger.info(f"Created MCP instance: {result}")
        
        if 'instanceId' not in result:
            raise ValueError("Response missing instanceId")
        if 'serverUrl' not in result:
            raise ValueError("Response missing serverUrl")
            
        return {
            'serverUrl': result['serverUrl'],
            'instanceId': result['instanceId']
        }
    
    def redirect_to_oauth(self, instance_id: str, server_name: ServerName) -> None:
        """
        Redirect to OAuth authorization page.
        
        Args:
            instance_id: ID of the MCP server instance
            server_name: Name of the target MCP server
        """
        service_path = OAUTH_SERVICE_NAME_TO_URL_PATH.get(server_name)
        if not service_path:
            # do not raise an error, skip it
            return

        oauth_url = f"{self.base_url}/oauth/{service_path}/authorize?instance_id={instance_id}"
        logger.info(f"Opening OAuth URL: {oauth_url}")
        webbrowser.open(oauth_url)
    
    def list_tools(self, server_url: str, connection_type: ConnectionType = "StreamableHttp") -> Dict[str, Any]:
        """
        List tools for a specific remote MCP server, used for function calling.
        
        Eliminates the need for manual MCP code implementation. Under the hood, 
        Klavis instantiates an MCP client and establishes a connection with the 
        remote MCP server to retrieve available tools.
        
        Args:
            server_url: URL of the server
            connection_type: The protocol to use for the MCP server (default: "StreamableHttp")
            
        Returns:
            Dictionary containing:
                - success: Whether the list tools request was successful
                - tools: List of tools available for the MCP server (or null if failed)
                - error: Error message if the request failed (or null if successful)
            
        Raises:
            RuntimeError: If the API request fails
        """
        params = {"connection_type": connection_type}
        encoded_server_url = urllib.parse.quote(server_url, safe='')
        result = self._make_request("GET", f"/mcp-server/list-tools/{encoded_server_url}", params=params)
        return result
    
    def call_tool(self, server_url: str, tool_name: str, 
                  tool_args: Optional[Dict[str, Any]] = None, 
                  connection_type: ConnectionType = "StreamableHttp") -> Dict[str, Any]:
        """
        Call a tool on a specific remote MCP server, used for function calling.
        
        Eliminates the need for manual MCP code implementation. Under the hood, 
        Klavis instantiates an MCP client and establishes a connection with the 
        remote MCP server to call the tool.
        
        Args:
            server_url: The full URL for connecting to the MCP server
            tool_name: The name of the tool to call
            tool_args: The input parameters for the tool (optional)
            connection_type: The protocol to use for the MCP server (default: "StreamableHttp")
            
        Returns:
            Dictionary containing:
                - success: Whether the API call was successful
                - result: The result of the tool call, if successful (or null if failed)
                - error: Error message, if the tool call failed (or null if successful)
            
        Raises:
            RuntimeError: If the API request fails
        """
        data = {
            "serverUrl": server_url,
            "toolName": tool_name,
            "toolArgs": tool_args or {},
            "connectionType": connection_type
        }
        
        result = self._make_request("POST", "/mcp-server/call-tool", json=data)
        logger.info(f"Called tool '{tool_name}'")
        return result
