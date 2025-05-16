import os
from klavis import ApiClient, Configuration
from klavis.api import McpServerApi
from klavis.models import CreateServerRequest, ServerName

def main():
    api_key = os.environ.get("KLAVIS_API_KEY", "YOUR_API_KEY") 
    if api_key == "YOUR_API_KEY":
        print("Warning: API Key not configured. Please set the KLAVIS_API_KEY environment variable or replace 'YOUR_API_KEY'.")

    config = Configuration(
        host="https://api.klavis.ai",
        api_key=api_key,
    )
    api_client = ApiClient(config)
    mcp_api = McpServerApi(api_client)
    
    create_request = CreateServerRequest(
        server_name=ServerName.GITHUB, 
        user_id="1234",
        platform_name="zihao_test"
    )
    instance = mcp_api.create_server_instance(create_request)
    
    print(instance.instance_id)

if __name__ == "__main__":
    main()
