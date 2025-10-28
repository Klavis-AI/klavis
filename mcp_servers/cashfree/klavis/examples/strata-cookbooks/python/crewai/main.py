import os
import webbrowser
from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from klavis import Klavis
from klavis.types import McpServerName

from dotenv import load_dotenv
load_dotenv()

klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

response = klavis_client.mcp_server.create_strata_server(
    servers=[McpServerName.GMAIL, McpServerName.SLACK], 
    user_id="1234"
)

# Handle OAuth authorization for each services
if response.oauth_urls:
    for server_name, oauth_url in response.oauth_urls.items():
        webbrowser.open(oauth_url)
        input(f"Or please open this URL to complete {server_name} OAuth authorization: {oauth_url}")

def crew_mcp_server(mcp_server_url: str, user_query: str):
    klavis_server_params = [
            {
                "url": mcp_server_url,
                "transport": "streamable-http"
            }
        ]

    with MCPServerAdapter(klavis_server_params) as all_mcp_tools:
        print(f"✅ Available tools: {[tool.name for tool in all_mcp_tools]}")

        klavis_agent = Agent(
            role="Klavis Query Assistant",
            goal="Assist the user with their query using available tools",
            backstory="Expert at assisting users with their queries using available tools",
            tools=all_mcp_tools,
            verbose=False,
            llm="gpt-4o"  # Using OpenAI GPT-4o model
        )

        klavis_task = Task(
            description=f"Answer the user's query: {user_query}",
            expected_output="Provide a detailed response to the user's query",
            agent=klavis_agent
        )

        crew = Crew(
            agents = [klavis_agent],
            tasks = [klavis_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        print(f"Crew result: {result}")

if __name__ == "__main__":
    user_query = "Check my latest 5 emails and summarize them in a Slack message to #general"  # Change this query as needed
    crew_mcp_server(response.strata_server_url,user_query)