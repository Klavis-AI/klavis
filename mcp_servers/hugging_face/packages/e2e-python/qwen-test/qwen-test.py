import asyncio
from mcp.types import PromptMessage
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("mcp server tests")

humans="""a man and woman are standing together against a backdrop, the backdrop is divided equally in half down the middle, left side is red, right side is gold, the woman is wearing a t-shirt with a yoda motif, she has a long skirt with birds on it, the man is wearing a three piece purple suit, he has spiky blue hair"""

# Define the agent
# @fast.agent(name="anon",instruction="You are a helpful AI Agent",servers=["anon_hf"])
@fast.agent(name="DVe0UTvm4",instruction="You are a helpful AI Agent",servers=["qwen"])


async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:

        await agent.interactive()
        prompt: PromptMessage =  await agent.DVe0UTvm4.get_prompt("Qwen Prompt Enhancer",{"prompt":"the man in the moon"})
        print(prompt)



if __name__ == "__main__":
    asyncio.run(main())
