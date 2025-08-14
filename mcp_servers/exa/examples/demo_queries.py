#!/usr/bin/env python3
"""
Demo queries for Exa MCP Server

This script demonstrates how to use each tool with example queries
that can be used for proof-of-correctness videos/screenshots.
"""

import asyncio
import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import initialize_server, tools_registry


async def demo_search_web():
    """Demonstrate search_web tool"""
    print("🔍 DEMO: search_web")
    print("-" * 40)
    
    tool = tools_registry["search_web"]
    
    # Example 1: General search
    print("Query: 'Find recent quantum computing research breakthroughs'")
    result = await tool.execute({
        "query": "quantum computing research breakthroughs 2024",
        "num_results": 3,
        "type": "neural"
    })
    print("✅ Result preview:", result[0].text[:200] + "...")
    print()
    
    # Example 2: Domain-filtered search
    print("Query: 'Python machine learning libraries' (filtered to GitHub)")
    result = await tool.execute({
        "query": "python machine learning libraries",
        "include_domains": ["github.com"],
        "num_results": 3
    })
    print("✅ Result preview:", result[0].text[:200] + "...")
    print()


async def demo_get_page_contents():
    """Demonstrate get_page_contents tool"""
    print("📄 DEMO: get_page_contents")
    print("-" * 40)
    
    # First, get a result ID from search
    search_tool = tools_registry["search_web"]
    search_result = await search_tool.execute({
        "query": "OpenAI GPT-4 technical report",
        "num_results": 1
    })
    
    # Extract result ID (this is a simplified extraction)
    import re
    id_match = re.search(r'ID: ([a-zA-Z0-9_-]+)', search_result[0].text)
    
    if id_match:
        result_id = id_match.group(1)
        print(f"Using result ID: {result_id}")
        
        # Get contents with summary
        content_tool = tools_registry["get_page_contents"]
        result = await content_tool.execute({
            "ids": [result_id],
            "text": True,
            "summary": True,
            "highlights": True
        })
        print("✅ Content preview:", result[0].text[:300] + "...")
    else:
        print("⚠️ Could not extract result ID from search")
    print()


async def demo_find_similar_content():
    """Demonstrate find_similar_content tool"""
    print("🔗 DEMO: find_similar_content")
    print("-" * 40)
    
    tool = tools_registry["find_similar_content"]
    
    print("Query: Find content similar to OpenAI's GPT-4 blog post")
    result = await tool.execute({
        "url": "https://openai.com/blog/gpt-4",
        "num_results": 3
    })
    print("✅ Result preview:", result[0].text[:200] + "...")
    print()


async def demo_search_recent_content():
    """Demonstrate search_recent_content tool"""
    print("📅 DEMO: search_recent_content")
    print("-" * 40)
    
    tool = tools_registry["search_recent_content"]
    
    print("Query: 'What's new in AI regulation this week?'")
    result = await tool.execute({
        "query": "AI regulation policy news",
        "days_back": 7,
        "num_results": 3
    })
    print("✅ Result preview:", result[0].text[:200] + "...")
    print()


async def demo_search_academic_content():
    """Demonstrate search_academic_content tool"""
    print("🎓 DEMO: search_academic_content")
    print("-" * 40)
    
    tool = tools_registry["search_academic_content"]
    
    print("Query: 'Find peer-reviewed papers on machine learning bias'")
    result = await tool.execute({
        "query": "machine learning algorithmic bias fairness",
        "num_results": 3
    })
    print("✅ Result preview:", result[0].text[:200] + "...")
    print()


async def run_all_demos():
    """Run all demo queries"""
    print("🎬 EXA MCP SERVER - DEMO QUERIES")
    print("=" * 50)
    print("These are the exact queries you can use for")
    print("your proof-of-correctness videos!")
    print("=" * 50)
    print()
    
    # Initialize server
    await initialize_server()
    
    demos = [
        demo_search_web,
        demo_get_page_contents,
        demo_find_similar_content,
        demo_search_recent_content,
        demo_search_academic_content
    ]
    
    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"❌ Demo failed: {str(e)}")
        
        print("─" * 50)
        print()
    
    print("🎉 Demo completed!")
    print("\n💡 Pro tips for recording:")
    print("1. Use these exact queries in your videos")
    print("2. Show the natural language input")
    print("3. Highlight the tool selection")
    print("4. Display the formatted results")
    print("5. Keep videos 30-60 seconds each")


def print_suggested_queries():
    """Print suggested queries for each tool"""
    print("📝 SUGGESTED QUERIES FOR PROOF VIDEOS")
    print("=" * 50)
    
    queries = {
        "search_web": [
            "Find recent quantum computing research breakthroughs",
            "Search for Python machine learning tutorials",
            "Look up information about sustainable energy technologies"
        ],
        "get_page_contents": [
            "Get the full content of that first research paper",
            "Extract the complete text from the quantum computing article",
            "Retrieve detailed content with summary from that result"
        ],
        "find_similar_content": [
            "Find content similar to https://openai.com/blog/gpt-4",
            "Discover pages related to that research paper",
            "Find similar articles to this blog post"
        ],
        "search_recent_content": [
            "What's new in AI regulation this week?",
            "Find recent developments in quantum computing",
            "Search for latest news about climate technology"
        ],
        "search_academic_content": [
            "Find peer-reviewed papers on machine learning bias",
            "Search for academic research on quantum algorithms",
            "Look up scholarly articles about renewable energy"
        ]
    }
    
    for tool, tool_queries in queries.items():
        print(f"\n🔧 {tool}:")
        for i, query in enumerate(tool_queries, 1):
            print(f"   {i}. {query}")
    
    print("\n💫 Remember: These queries show the natural language")
    print("interface that makes your MCP server so powerful!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Exa MCP Server Demo Queries")
    parser.add_argument("--run", action="store_true", help="Run live demos")
    parser.add_argument("--queries", action="store_true", help="Show suggested queries")
    
    args = parser.parse_args()
    
    if args.run:
        asyncio.run(run_all_demos())
    elif args.queries:
        print_suggested_queries()
    else:
        print("Usage:")
        print("  python demo_queries.py --run      # Run live demos")
        print("  python demo_queries.py --queries  # Show suggested queries")
        print_suggested_queries()