import asyncio
import csv
from datetime import datetime

from fast_agent import FastAgent, ConversationSummary, extract_last
import huggingface_hub
import os
from fast_agent.mcp.prompt_serialization import save_messages
# Create the application
fast = FastAgent("fast-agent example")


default_instruction = """You are a helpful AI Agent.

{{serverInstructions}}

{{agentSkills}}

The current date is {{currentDate}}."""

@fast.agent(name="jobs", instruction=default_instruction, servers=["live_hf"])
async def main():
    # Setup CSV file with comprehensive metrics
    csv_filename = "evaluation_results.csv"
    fieldnames = [
        "run_number",
        "model",
        "tool_calls",
        "tool_errors",
        "hf_jobs_calls",
        "other_calls",
        "tokens",
        "status",
        "job_id",
        "conversation_span_ms",     # First LLM call → Last LLM call  
    ]
    
    timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")

    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(1, 2):
            async with fast.run() as agent:
                jobs = agent.jobs
                
                await jobs.send(
                    "run a job to print 'hello world' and a 2 digit random number to the console"
                )
                model_name = jobs.llm.model_name
                assert model_name is not None
                model_short = model_name.split("/")[-1]
                summary = ConversationSummary(messages=jobs.message_history)

                job_id = extract_last(
                    jobs.message_history,
                    r"Job started: ([a-f0-9]+)",
                    scope="tool_results",
                    group=1
                )

                # Check job status
                status = "UNDETERMINED"
                if job_id:
                    status = huggingface_hub.HfApi(
                        token=os.environ.get("HF_TEST_TOKEN")
                    ).inspect_job(job_id=job_id).status.stage
                    print(f"Run {i}: {status}")

                tool_map = summary.tool_call_map
                hf_jobs_calls = tool_map.get("live_hf__hf_jobs", 0)
                other_calls = summary.tool_calls - hf_jobs_calls

                # Write row with all metrics
                row = {
                    "run_number": i,
                    "model": jobs.llm.model_name,
                    "tool_calls": summary.tool_calls,
                    "tool_errors": summary.tool_errors,
                    "hf_jobs_calls": hf_jobs_calls,
                    "other_calls": other_calls,
                    "tokens": (
                        jobs.llm.usage_accumulator.cumulative_billing_tokens
                        if jobs.llm.usage_accumulator
                        else 0
                    ),
                    "status": status,
                    "job_id": job_id,
                    "conversation_span_ms": summary.conversation_span_ms,
                }
                writer.writerow(row)
                csvfile.flush()  # Write immediately to disk

                history_filename = f"{timestamp}_{model_short}_run_{i}.json"
                save_messages(jobs.message_history, history_filename)
    
    print(f"\nResults written to {csv_filename}")

if __name__ == "__main__":
    asyncio.run(main())
