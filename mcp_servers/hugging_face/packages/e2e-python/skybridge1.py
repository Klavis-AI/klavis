import asyncio
from fast_agent import FastAgent
from fast_agent.mcp.skybridge import SkybridgeServerConfig
# Create the application
fast = FastAgent("mcp server tests")


# Define the agent
@fast.agent(name="skybridge",instruction="You are a helpful AI Agent",servers=["skybridge"])

async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()

        hf_config: SkybridgeServerConfig  = await agent.skybridge._aggregator.get_skybridge_config("skybridge")
        for res in hf_config.ui_resources:
            content = await agent.skybridge.get_resource(str(res.uri))
            print(content.contents[0])
        await agent.interactive()



if __name__ == "__main__":
    asyncio.run(main())
