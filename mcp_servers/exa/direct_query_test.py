#!/usr/bin/env python3
"""
Direct query testing for Exa MCP Server
This script lets you test individual tools directly - Perfect for recording demos!
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def demo_search_web():
    """Test the search_web tool - PERFECT FOR VIDEO 1"""
    print("🔍 VIDEO 1: search_web")
    print("=" * 50)
    print("Query: 'Find recent quantum computing research breakthroughs'")
    print("-" * 50)
    
    # Import and use tools directly
    from src.main import call_tool
    
    result = await call_tool("search_web", {
        "query": "quantum computing research breakthroughs 2024",
        "num_results": 5,
        "type": "neural"
    })
    
    print("✅ RESULT:")
    print(result[0].text)
    print("\n" + "="*60 + "\n")
    
    # Return first result ID for next demo
    import re
    id_match = re.search(r'ID: ([a-zA-Z0-9_-]+)', result[0].text)
    return id_match.group(1) if id_match else None


async def demo_get_page_contents(result_id=None):
    """Test the get_page_contents tool - PERFECT FOR VIDEO 2"""
    print("📄 VIDEO 2: get_page_contents")
    print("=" * 50)
    print("Query: 'Get the full content from that first research result with summary'")
    print("-" * 50)
    
    from src.main import call_tool
    
    if not result_id:
        # Get a result ID first
        search_result = await call_tool("search_web", {
            "query": "OpenAI GPT research",
            "num_results": 1
        })
        
        import re
        id_match = re.search(r'ID: ([a-zA-Z0-9_-]+)', search_result[0].text)
        result_id = id_match.group(1) if id_match else "fallback_id"
    
    print(f"Using result ID: {result_id}")
    
    result = await call_tool("get_page_contents", {
        "ids": [result_id],
        "text": True,
        "summary": True,
        "highlights": True
    })
    
    print("✅ RESULT:")
    print(result[0].text[:800] + "..." if len(result[0].text) > 800 else result[0].text)
    print("\n" + "="*60 + "\n")


async def demo_find_similar():
    """Test the find_similar_content tool - PERFECT FOR VIDEO 3"""
    print("🔗 VIDEO 3: find_similar_content")
    print("=" * 50)
    print("Query: 'Find content similar to https://openai.com/blog/gpt-4'")
    print("-" * 50)
    
    from src.main import call_tool
    
    result = await call_tool("find_similar_content", {
        "url": "https://openai.com/blog/gpt-4",
        "num_results": 5
    })
    
    print("✅ RESULT:")
    print(result[0].text)
    print("\n" + "="*60 + "\n")


async def demo_search_recent():
    """Test the search_recent_content tool - PERFECT FOR VIDEO 4"""
    print("📅 VIDEO 4: search_recent_content")
    print("=" * 50)
    print("Query: 'What's new in AI regulation this week?'")
    print("-" * 50)
    
    from src.main import call_tool
    
    result = await call_tool("search_recent_content", {
        "query": "AI regulation policy news",
        "days_back": 7,
        "num_results": 5
    })
    
    print("✅ RESULT:")
    print(result[0].text)
    print("\n" + "="*60 + "\n")


async def demo_search_academic():
    """Test the search_academic_content tool - PERFECT FOR VIDEO 5"""
    print("🎓 VIDEO 5: search_academic_content")
    print("=" * 50)
    print("Query: 'Find peer-reviewed papers on machine learning bias'")
    print("-" * 50)
    
    from src.main import call_tool
    
    result = await call_tool("search_academic_content", {
        "query": "machine learning algorithmic bias fairness",
        "num_results": 5
    })
    
    print("✅ RESULT:")
    print(result[0].text)
    print("\n" + "="*60 + "\n")


async def run_all_video_demos():
    """Run all video demos in sequence"""
    print("🎬 EXA MCP SERVER - VIDEO RECORDING DEMOS")
    print("=" * 60)
    print("📹 Record each section for your proof videos!")
    print("=" * 60)
    print()
    
    try:
        print("✅ Ready to record!\n")
        
        # Demo 1: Search Web
        result_id = await demo_search_web()
        
        # Demo 2: Get Page Contents  
        await demo_get_page_contents(result_id)
        
        # Demo 3: Find Similar Content
        await demo_find_similar()
        
        # Demo 4: Search Recent Content
        await demo_search_recent()
        
        # Demo 5: Search Academic Content
        await demo_search_academic()
        
        print("🎉 ALL DEMOS COMPLETED!")
        print("\n💡 Recording Tips:")
        print("- Each demo above is perfect for one video")
        print("- Show the query, execution, and formatted results")
        print("- Keep each video 30-60 seconds")
        print("- Highlight the AI-friendly responses")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your EXA_API_KEY is set")
        print("2. Verify internet connection")
        print("3. Run: python tests/test_integration.py")


async def interactive_demo():
    """Interactive demo mode"""
    print("🎮 INTERACTIVE DEMO MODE")
    print("=" * 40)
    print("Choose which demo to run:")
    print("1. search_web (Video 1)")
    print("2. get_page_contents (Video 2)")
    print("3. find_similar_content (Video 3)")
    print("4. search_recent_content (Video 4)")
    print("5. search_academic_content (Video 5)")
    print("6. Run all demos")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        await demo_search_web()
    elif choice == "2":
        await demo_get_page_contents()
    elif choice == "3":
        await demo_find_similar()
    elif choice == "4":
        await demo_search_recent()
    elif choice == "5":
        await demo_search_academic()
    elif choice == "6":
        await run_all_video_demos()
    else:
        print("Invalid choice")


async def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        await run_all_video_demos()
    else:
        await interactive_demo()


if __name__ == "__main__":
    asyncio.run(main())