#!/usr/bin/env python3
"""
Test script for custom MCP tools. I had originally added many more tools (They're innthe code files) from Elevnlabs, Serp, and Tavily, to see if I could integrate multiple services into the server, but I had to limit it to 40 tools due to Cursor's limit. 35 are from replicate's direct MCP integration with Cursor, and 5 are from my own custom tools.
"""

def test_custom_tools():
    # Test all custom tools
    print("🧪 Testing Custom MCP Tools")
    print("=" * 40)
    
    # Web Search Test
    print("1. Testing web search...")
    try:
        from tools.serpapi_search import search_web_query
        result = search_web_query("latest AI news", 2)
        print(f"   ✅ Web search: {result.get('success', False)}")
        if result.get('success'):
            print(f"   📊 Found {len(result.get('organic_results', []))} results")
    except Exception as e:
        print(f"   ❌ Web search failed: {e}")
    
    # Voice Generation Test
    print("\n2. Testing voice generation...")
    try:
        from tools.elevenlabs_voice import generate_voice_from_text
        result = generate_voice_from_text("Hello, this is a test.")
        print(f"   ✅ Voice generation: {result.get('success', False)}")
        if result.get('success'):
            print(f"   🎵 Audio saved to: {result.get('audio_path', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Voice generation failed: {e}")
    
    # Tavily Search Test
    print("\n3. Testing Tavily search...")
    try:
        from tools.tavily_search import search_with_tavily
        result = search_with_tavily("artificial intelligence", "basic")
        print(f"   ✅ Tavily search: {result.get('success', False)}")
        if result.get('success'):
            print(f"   📊 Found {len(result.get('results', []))} results")
    except Exception as e:
        print(f"   ❌ Tavily search failed: {e}")
    
    # Webpage Summarization Test
    print("\n4. Testing webpage summarization...")
    try:
        from tools.tavily_search import summarize_webpage
        result = summarize_webpage("https://techcrunch.com/")
        print(f"   ✅ Summarization: {result.get('success', False)}")
        if result.get('success'):
            print(f"   📝 Summary: {result.get('summary', '')[:100]}...")
    except Exception as e:
        print(f"   ❌ Summarization failed: {e}")
    
    # Image, infographic Generation Test
    print("\n5. Testing image generation...")
    try:
        from tools.generate_image import generate_image
        result = generate_image("A beautiful sunset over mountains")
        print(f"   ✅ Image generation: {result is not None}")
        if result:
            print(f"   🖼️  Image URL: {result}")
    except Exception as e:
        print(f"   ❌ Image generation failed: {e}")
    
    print("\n" + "=" * 40)
    print("Custom tools test completed!")
    print("If all tests passed, your MCP tools should work in Cursor!")
    print("\n📋 Available Tools:")
    print("   • generate_voice - ElevenLabs voice generation")
    print("   • search_web - SerpAPI web search")
    print("   • search_tavily - Tavily advanced search")
    print("   • summarize_webpage - Tavily summarization")
    print("   • generate_image - Replicate image generation")

def demo_usage():
    # Show example usage of the tools
    print("\n" + "=" * 40)
    print("🎯 DEMO USAGE EXAMPLES")
    print("=" * 40)
    
    print("1. Voice Generation:")
    print("   generate_voice('Hello world', 'voice_id')")
    
    print("\n2. Web Search:")
    print("   search_web('latest AI news', 5)")
    
    print("\n3. Advanced Search:")
    print("   search_tavily('artificial intelligence trends', 'basic')")
    
    print("\n4. Webpage Summarization:")
    print("   summarize_webpage('https://example.com')")
    
    print("\n5. Image Generation:")
    print("   generate_image('A beautiful sunset over mountains')")
    
    print("\n" + "=" * 40)
    print("🚀 All tools are ready for MCP integration!")

if __name__ == "__main__":
    test_custom_tools()
    demo_usage()

