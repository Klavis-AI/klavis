import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("mcp server tests")


# Define the agent
# @fast.agent(name="anon",instruction="You are a helpful AI Agent",servers=["anon_hf"])
@fast.agent(name="DVe0UTvm4",instruction="You are a helpful AI Agent",servers=["test_hf"])

async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:

#        print(await agent.DVe0UTvm4.call_tool("hf_whoami",{}))
 #       print(await agent.DVe0UTvm4.call_tool("test_hf-hf_whoami",{}))
        await agent.interactive()



if __name__ == "__main__":
    asyncio.run(main())
