"""
Multi-Service Crew with Salesforce and Gmail Integration
Demonstrates CrewAI + Klavis MCP servers for Salesforce opportunity management and Gmail communication
"""

import os
import webbrowser
from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from klavis import Klavis
from klavis.types import McpServerName, ConnectionType


def multi_server_crew():
    """Main function to execute the multi-service Salesforce crew"""
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    try:
        # Step 1: Create Salesforce MCP Server
        salesforce_mcp_instance = klavis_client.mcp_server.create_server_instance(
            server_name=McpServerName.SALESFORCE,
            user_id="1234",
            platform_name="Klavis",
            connection_type=ConnectionType.STREAMABLE_HTTP,
        )
        webbrowser.open(salesforce_mcp_instance.oauth_url)
        
        input("Press Enter after OAuth...")
        
        # Step 2: Create Gmail MCP Server
        gmail_mcp_instance = klavis_client.mcp_server.create_server_instance(
            server_name=McpServerName.GMAIL,
            user_id="1234",
            platform_name="Klavis",
            connection_type=ConnectionType.STREAMABLE_HTTP,
        )
        webbrowser.open(gmail_mcp_instance.oauth_url)

        input("Press Enter after OAuth...")
        
        # Step 3: Configure MCP servers via CrewAI
        salesforce_mcp_server = MCPServerAdapter({
            "url": salesforce_mcp_instance.server_url,
            "transport": "streamable-http"
        })
        
        gmail_mcp_server = MCPServerAdapter({
            "url": gmail_mcp_instance.server_url,
            "transport": "streamable-http"
        })
        
        try:
            # Salesforce Agent
            salesforce_agent = Agent(
                role="Salesforce Opportunity Analyst",
                goal="Find opportunities with pending next steps",
                backstory="Expert at finding Salesforce opportunities that need follow-up actions",
                tools=salesforce_mcp_server.tools,
                verbose=False,
            )
            
            # Email Agent
            email_agent = Agent(
                role="Email Specialist",
                goal="Draft follow-up emails based on Salesforce Opportunity next steps",
                backstory="Expert at drafting complete, professional follow-up emails without placeholder content. Always writes proper signatures and complete email content.",
                tools=gmail_mcp_server.tools,
                verbose=False,
            )
            
            # Tasks
            salesforce_task = Task(
                description="Find OpenAI opportunities with next steps. Extract opportunity name, next step details, and contact emails.",
                expected_output="List of opportunities with next steps and contact information",
                agent=salesforce_agent
            )
            
            email_task = Task(
                description="Draft professional follow-up emails based on the Salesforce next steps. Include opportunity context and clear next actions. ",
                expected_output="Draft email with complete content ready for review",
                agent=email_agent
            )
            
            # Execute crew
            crew = Crew(
                agents=[salesforce_agent, email_agent],
                tasks=[salesforce_task, email_task],
                process=Process.sequential,
                verbose=True,
            )
            
            result = crew.kickoff()
            print(result)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            salesforce_mcp_server.stop()
            gmail_mcp_server.stop()
            
    except Exception as e:
        print(f"Setup Error: {e}")


if __name__ == "__main__":
    multi_server_crew() 