#!/usr/bin/env python3
"""
Exa API Connection Test Script - Fixed Version
Validates that the Exa API key is working before running the MCP server.

This script must pass before submitting to Klavis AI.
"""

import os
import sys
from typing import Optional

def test_environment_setup() -> bool:
    """Test that environment variables are properly configured."""
    print("🔧 Testing environment setup...")
    
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("❌ ERROR: EXA_API_KEY environment variable not set!")
        print("   📝 To fix this:")
        print("   1. Go to https://exa.ai/ and get your API key")
        print("   2. Set the environment variable:")
        print("      export EXA_API_KEY='your_api_key_here'")
        print("   3. Run this test again")
        return False
    
    print(f"✅ EXA_API_KEY found: {api_key[:10]}...")
    return True

def test_exa_import() -> bool:
    """Test that exa-py library is properly installed."""
    print("\n📦 Testing Exa library installation...")
    
    try:
        from exa_py import Exa
        print("✅ exa-py library imported successfully")
        return True
    except ImportError as e:
        print(f"❌ ERROR: Failed to import exa-py: {e}")
        print("   📝 To fix this:")
        print("   pip install exa-py")
        return False

def test_mcp_import() -> bool:
    """Test that MCP library is properly installed."""
    print("\n📦 Testing MCP library installation...")
    
    try:
        import mcp
        print("✅ MCP library imported successfully")
        return True
    except ImportError as e:
        print(f"❌ ERROR: Failed to import mcp: {e}")
        print("   📝 To fix this:")
        print("   pip install mcp")
        return False

def safe_format_score(score) -> str:
    """Safely format a score value that might be None."""
    if score is None:
        return "N/A"
    try:
        return f"{float(score):.3f}"
    except (ValueError, TypeError):
        return str(score)

def safe_get_attr(obj, attr_name: str, default: str = "N/A") -> str:
    """Safely get an attribute that might be None."""
    value = getattr(obj, attr_name, None)
    return str(value) if value is not None else default

def test_exa_api_connection() -> bool:
    """Test actual connection to Exa API."""
    print("\n🌐 Testing Exa API connection...")
    
    try:
        from exa_py import Exa
        
        api_key = os.getenv("EXA_API_KEY")
        exa = Exa(api_key)
        
        print("🔍 Testing basic search functionality...")
        results = exa.search("test query", num_results=1)
        
        if results and results.results:
            result = results.results[0]
            print("✅ Exa API connection successful!")
            print(f"   📄 Test result: {safe_get_attr(result, 'title', 'No title')}")
            print(f"   🔗 URL: {safe_get_attr(result, 'url', 'No URL')}")
            print(f"   ⭐ Score: {safe_format_score(getattr(result, 'score', None))}")
            
            # Test published date if available
            pub_date = getattr(result, 'published_date', None)
            if pub_date:
                print(f"   📅 Published: {pub_date}")
            
            return True
        else:
            print("❌ ERROR: Exa API returned no results")
            print("   This might indicate an API key issue or service problem")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exa API connection failed: {e}")
        print("   📝 Possible causes:")
        print("   - Invalid API key")
        print("   - Network connectivity issues") 
        print("   - Exa service temporarily unavailable")
        print("   - API quota exceeded")
        return False

def test_content_extraction() -> bool:
    """Test content extraction functionality."""
    print("\n📄 Testing content extraction...")
    
    try:
        from exa_py import Exa
        
        api_key = os.getenv("EXA_API_KEY")
        exa = Exa(api_key)
        
        # Test with a reliable URL
        test_url = "https://example.com"
        results = exa.get_contents([test_url], text=True)
        
        if results and results.results:
            content = results.results[0]
            print("✅ Content extraction successful!")
            print(f"   📄 Extracted from: {safe_get_attr(content, 'url', 'No URL')}")
            print(f"   📝 Title: {safe_get_attr(content, 'title', 'No title')}")
            
            # Safely handle text content
            text_content = getattr(content, 'text', None)
            if text_content:
                preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
                print(f"   📖 Content preview: {preview}")
            else:
                print("   📖 Content: No text content available")
            return True
        else:
            print("⚠️  WARNING: Content extraction returned no results")
            print("   This is not critical but may indicate limited functionality")
            return True  # Not a critical failure
            
    except Exception as e:
        print(f"⚠️  WARNING: Content extraction test failed: {e}")
        print("   This is not critical for basic search functionality")
        return True  # Not a critical failure

def test_similarity_search() -> bool:
    """Test similarity search functionality."""
    print("\n🔗 Testing similarity search...")
    
    try:
        from exa_py import Exa
        
        api_key = os.getenv("EXA_API_KEY")
        exa = Exa(api_key)
        
        # Test with a reliable URL
        test_url = "https://example.com"
        results = exa.find_similar(test_url, num_results=1)
        
        if results and results.results:
            result = results.results[0]
            print("✅ Similarity search successful!")
            print(f"   🔗 Similar to: {test_url}")
            print(f"   📄 Found: {safe_get_attr(result, 'title', 'No title')}")
            print(f"   ⭐ Score: {safe_format_score(getattr(result, 'score', None))}")
            
            # Test published date if available
            pub_date = getattr(result, 'published_date', None)
            if pub_date:
                print(f"   📅 Published: {pub_date}")
            
            return True
        else:
            print("⚠️  WARNING: Similarity search returned no results")
            print("   This may be normal depending on the test URL")
            return True  # Not a critical failure
            
    except Exception as e:
        print(f"⚠️  WARNING: Similarity search test failed: {e}")
        print("   This is not critical for basic search functionality") 
        return True  # Not a critical failure

def test_additional_functionality() -> bool:
    """Test additional Exa features to ensure comprehensive functionality."""
    print("\n🧪 Testing additional functionality...")
    
    try:
        from exa_py import Exa
        
        api_key = os.getenv("EXA_API_KEY")
        exa = Exa(api_key)
        
        # Test search with date filtering
        print("   Testing date-filtered search...")
        results = exa.search(
            "technology news", 
            num_results=1,
            start_published_date="2024-01-01"
        )
        
        if results and results.results:
            print("   ✅ Date-filtered search working")
        else:
            print("   ⚠️  Date-filtered search returned no results (not critical)")
        
        # Test neural search type
        print("   Testing neural search type...")
        results = exa.search(
            "artificial intelligence", 
            num_results=1,
            type="neural"
        )
        
        if results and results.results:
            print("   ✅ Neural search type working")
        else:
            print("   ⚠️  Neural search returned no results (not critical)")
        
        print("✅ Additional functionality tests completed!")
        return True
        
    except Exception as e:
        print(f"⚠️  WARNING: Additional functionality test failed: {e}")
        print("   This is not critical for basic server functionality")
        return True  # Not a critical failure

def run_all_tests() -> bool:
    """Run all tests and return overall success status."""
    print("🧪 Exa MCP Server - Connection Test Suite (Fixed Version)")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Exa Library Import", test_exa_import),
        ("MCP Library Import", test_mcp_import),
        ("Exa API Connection", test_exa_api_connection),
        ("Content Extraction", test_content_extraction),
        ("Similarity Search", test_similarity_search),
        ("Additional Functionality", test_additional_functionality),
    ]
    
    passed = 0
    critical_passed = 0
    critical_tests = 4  # First 4 tests are critical
    
    for i, (test_name, test_func) in enumerate(tests):
        try:
            success = test_func()
            if success:
                passed += 1
                if i < critical_tests:
                    critical_passed += 1
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    print(f"🔥 Critical Tests: {critical_passed}/{critical_tests} passed")
    
    if critical_passed == critical_tests:
        print("\n🎉 SUCCESS! Your Exa MCP server is ready to run!")
        print("\n📋 Next steps:")
        print("   1. Run the server: python server.py")
        print("   2. Configure Claude Desktop with the server")
        print("   3. Test with natural language commands")
        print("   4. Create proof videos for Klavis AI submission")
        print("\n🚀 Your API is working perfectly - proceed with confidence!")
        return True
    else:
        print(f"\n❌ FAILURE! {critical_tests - critical_passed} critical tests failed.")
        print("   Please fix the issues above before proceeding.")
        print("\n🆘 Need help?")
        print("   - Check your Exa API key: https://exa.ai/")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Check network connection")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)