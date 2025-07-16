"""
Multi-Service Crew with YouTube and Gmail Integration
Demonstrates CrewAI + Klavis MCP servers for YouTube research and Gmail communication
"""

import os
import webbrowser
from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from klavis import Klavis
from klavis.types import McpServerName

VIDEO_URL = "https://www.youtube.com/watch?v=LCEmiRjPEtQ"  # Change to your desired video
RECIPIENT_EMAIL = "zihaolin@klavis.ai"  # Replace with your email

def main():
    """Main function to execute the multi-service research crew"""
    print(f"Klavis API key: {os.getenv('KLAVIS_API_KEY')}")
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    try:
        # Step 1: Create YouTube MCP Server
        youtube_mcp_instance = klavis_client.mcp_server.create_server_instance(
            server_name=McpServerName.YOUTUBE,
            user_id="1234",
            platform_name="Klavis",
        )
        print(f"✅ YouTube MCP server created: {youtube_mcp_instance.server_url}")
        
        # Step 2: Create Gmail MCP Server (OAuth required)
        gmail_mcp_instance = klavis_client.mcp_server.create_server_instance(
            server_name=McpServerName.GMAIL,
            user_id="1234",
            platform_name="Klavis",
        )
        webbrowser.open(gmail_mcp_instance.oauth_url)
        
        print(f"📱 If you are not redirected to the Gmail OAuth page, please open it manually: {gmail_mcp_instance.oauth_url}")
        
        # Step 3: Configure multiple MCP servers
        multiple_server_params = [
            {
                "url": youtube_mcp_instance.server_url,
                "transport": "streamable-http"
            },
            {
                "url": gmail_mcp_instance.server_url,
                "transport": "streamable-http"
            }
        ]
        
        # Step 4: Create and execute the multi-service crew
        with MCPServerAdapter(multiple_server_params) as all_mcp_tools:
            print(f"✅ Available tools: {[tool.name for tool in all_mcp_tools]}")
            
            # Create YouTube Analysis Agent
            youtube_analysis_agent = Agent(
                role="YouTube Content Analyst",
                goal="Research and analyze YouTube videos to extract comprehensive insights and create structured summaries with timestamps",
                backstory="You are an expert at analyzing video content, extracting transcripts with precise timestamps, and creating professional summaries with key insights, takeaways, and time-coded references for easy navigation.",
                tools=all_mcp_tools,
                reasoning=False,
                verbose=False,
            )
            
            # Create Email Agent
            email_agent = Agent(
                role="Email Communications Specialist",
                goal="Draft and send professional email communications based on research findings",
                backstory="You are skilled at crafting professional emails and managing correspondence with clear, impactful messaging.",
                tools=all_mcp_tools,
                reasoning=True,
                verbose=False,
            )
            
            # Define workflow tasks
            youtube_analysis_task = Task(
                description=f"Research the YouTube video at {VIDEO_URL}. Extract transcript, analyze the content for key insights about AI and software development, and create a comprehensive analysis report with key takeaways and recommendations.",
                expected_output="Complete video analysis report with transcript, key insights, recommendations, and strategic takeaways",
                agent=youtube_analysis_agent
            )
            
            send_email_task = Task(
                description=f"Based on the youtube analysis, draft and send a professional email to {RECIPIENT_EMAIL} with the subject 'YouTube Video AI Analysis'. Include content of the youtube video in the email.",
                expected_output="Confirmation that a professional email has been sent with the research insights",
                agent=email_agent,
                context=[youtube_analysis_task]
            )
            
            # Create and execute the crew
            multi_service_crew = Crew(
                agents=[youtube_analysis_agent, email_agent],
                tasks=[youtube_analysis_task, send_email_task],
                verbose=True,  # Set to False to reduce output
                process=Process.sequential
            )
            
            result = multi_service_crew.kickoff()
            
            print(result)
            
    except Exception as e:
        print(f"Error with multi-service MCP integration: {e}")


if __name__ == "__main__":
    main() 