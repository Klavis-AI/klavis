import asyncio
from fast_agent import FastAgent

# Create the application
fast = FastAgent("mcp server tests")


# Define the agent
@fast.agent(name="anon",instruction="You are a helpful AI Agent",servers=["anon_hf"])
@fast.agent(name="DVe0UTvm4",instruction="You are a helpful AI Agent",servers=["test_hf"])
@fast.agent(name="all",instruction="You are a helpful AI Agent",servers=["test_all_hf"])

async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()


        # anonymous tool calling
        await agent.anon("***CALL_TOOL hf_whoami {}")
        await agent.anon("***CALL_TOOL model_search {}")
        await agent.anon('***CALL_TOOL model_search {"author": "zai-org", "limit": 3}')
        await agent.anon('***CALL_TOOL dataset_search {"author": "zai-org", "limit": 3}')
        await agent.anon('***CALL_TOOL space_search {"query": "evalstate", "limit": 3,"mcp": true}')
        await agent.anon('***CALL_TOOL hf_doc_search {"query": "transformers"}')

        # authenticated test account
        await agent.DVe0UTvm4('***CALL_TOOL hf_doc_search {"query": "transformers"}')
        await agent.DVe0UTvm4('***CALL_TOOL model_search {"query": "qwen"}')


        # authenticated, all tools (excluding duplicate space for now)
        await agent.all('***CALL_TOOL model_details {"model_id": "transformers"}')
        await agent.all('***CALL_TOOL dataset_details {"dataset_id": "qwen"}')
        await agent.all('***CALL_TOOL hf_doc_search {"query": "transformers"}')
        await agent.all('***CALL_TOOL hf_doc_fetch {"doc_url": "https://huggingface.co/docs/huggingface_hub/guides/upload"}')
        await agent.all('***CALL_TOOL paper_search {"query": "llama","limit": 3}')
        await agent.all('***CALL_TOOL space_info {}')

        # prompt application
        await agent.anon.apply_prompt("User Summary",{"user_id": "DVe0UTvm4"})
        await agent.anon.apply_prompt("Paper Summary",{"paper_id": "arxiv:2502.16161"})


if __name__ == "__main__":
    asyncio.run(main())
