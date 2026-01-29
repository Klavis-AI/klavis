import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("mcp server tests")


# Define the agent
@fast.agent(name="anon",instruction="You are a helpful AI Agent",servers=["anon_hf"])

async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()


        # anonymous tool calling
        await agent.anon("***CALL_TOOL hf_whoami {}")

        await agent.anon.apply_prompt("Model Details",{"model_id": "openai/gpt-oss-120b"})
        await agent.anon.apply_prompt("Dataset Details",{"dataset_id": "Anthropic/hh-rlhf"})

        # prompt application
        await agent.anon.apply_prompt("User Summary",{"user_id": "DVe0UTvm4"})
        await agent.anon.apply_prompt("Paper Summary",{"paper_id": "arxiv:2502.16161"})


if __name__ == "__main__":
    asyncio.run(main())
