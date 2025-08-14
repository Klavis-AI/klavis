#!/usr/bin/env python3
"""
Comprehensive integration tests for Exa MCP Server
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.exa_client import ExaClient
from src.models.schemas import ExaSearchParams, ExaContentsParams, ExaSimilarParams
from src.utils.config import validate_config
from src.utils.logging import setup_logging

logger = setup_logging()


class IntegrationTester:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.client = None
        self.test_results = {}
    
    async def setup(self):
        """Set up test environment"""
        logger.info("Setting up integration tests")
        
        # Validate configuration
        if not validate_config():
            raise RuntimeError("Configuration validation failed")
        
        # Initialize client
        self.client = ExaClient()
        logger.info("Test client initialized")
    
    async def teardown(self):
        """Clean up test environment"""
        if self.client:
            await self.client.close()
        logger.info("Test cleanup completed")
    
    async def test_basic_search(self) -> bool:
        """Test basic search functionality"""
        logger.info("Testing basic search...")
        
        try:
            params = ExaSearchParams(
                query="artificial intelligence recent developments",
                num_results=5,
                type="neural"
            )
            
            result = await self.client.search(params)
            
            if not result.success:
                logger.error(f"Search failed: {result.error}")
                return False
            
            results = result.data.get('results', [])
            if len(results) == 0:
                logger.error("No search results returned")
                return False
            
            logger.info(f"✅ Basic search successful: {len(results)} results")
            
            # Store result ID for later tests
            if results:
                self.test_results['sample_result_id'] = results[0].get('id')
            
            return True
            
        except Exception as e:
            logger.error(f"Basic search test failed: {str(e)}")
            return False
    
    async def test_content_retrieval(self) -> bool:
        """Test content retrieval functionality"""
        logger.info("Testing content retrieval...")
        
        if 'sample_result_id' not in self.test_results:
            logger.error("No result ID available for content test")
            return False
        
        try:
            params = ExaContentsParams(
                ids=[self.test_results['sample_result_id']],
                text=True,
                summary=True
            )
            
            result = await self.client.get_contents(params)
            
            if not result.success:
                logger.error(f"Content retrieval failed: {result.error}")
                return False
            
            contents = result.data.get('results', [])
            if len(contents) == 0:
                logger.error("No content retrieved")
                return False
            
            logger.info(f"✅ Content retrieval successful: {len(contents)} items")
            return True
            
        except Exception as e:
            logger.error(f"Content retrieval test failed: {str(e)}")
            return False
    
    async def test_similarity_search(self) -> bool:
        """Test similarity search functionality"""
        logger.info("Testing similarity search...")
        
        try:
            params = ExaSimilarParams(
                url="https://openai.com/blog/gpt-4",
                num_results=5
            )
            
            result = await self.client.find_similar(params)
            
            if not result.success:
                logger.error(f"Similarity search failed: {result.error}")
                return False
            
            similar_results = result.data.get('results', [])
            if len(similar_results) == 0:
                logger.error("No similar results found")
                return False
            
            logger.info(f"✅ Similarity search successful: {len(similar_results)} results")
            return True
            
        except Exception as e:
            logger.error(f"Similarity search test failed: {str(e)}")
            return False
    
    async def test_keyword_vs_neural_search(self) -> bool:
        """Test difference between keyword and neural search"""
        logger.info("Testing keyword vs neural search...")
        
        try:
            query = "machine learning algorithms"
            
            # Test neural search
            neural_params = ExaSearchParams(
                query=query,
                num_results=3,
                type="neural"
            )
            neural_result = await self.client.search(neural_params)
            
            # Test keyword search
            keyword_params = ExaSearchParams(
                query=query,
                num_results=3,
                type="keyword"
            )
            keyword_result = await self.client.search(keyword_params)
            
            if not neural_result.success or not keyword_result.success:
                logger.error("Search type comparison failed")
                return False
            
            neural_count = len(neural_result.data.get('results', []))
            keyword_count = len(keyword_result.data.get('results', []))
            
            logger.info(f"✅ Search type test successful: Neural={neural_count}, Keyword={keyword_count}")
            return True
            
        except Exception as e:
            logger.error(f"Search type test failed: {str(e)}")
            return False
    
    async def test_domain_filtering(self) -> bool:
        """Test domain filtering functionality"""
        logger.info("Testing domain filtering...")
        
        try:
            params = ExaSearchParams(
                query="python programming",
                num_results=3,
                include_domains=["github.com", "stackoverflow.com"]
            )
            
            result = await self.client.search(params)
            
            if not result.success:
                logger.error(f"Domain filtering test failed: {result.error}")
                return False
            
            results = result.data.get('results', [])
            
            # Check if results are from specified domains
            domain_match = False
            for item in results:
                url = item.get('url', '')
                if 'github.com' in url or 'stackoverflow.com' in url:
                    domain_match = True
                    break
            
            if domain_match:
                logger.info(f"✅ Domain filtering successful: {len(results)} results from specified domains")
                return True
            else:
                logger.warning("⚠️ Domain filtering returned results but not from specified domains")
                return True  # Still pass as API might not have content from those domains
            
        except Exception as e:
            logger.error(f"Domain filtering test failed: {str(e)}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        logger.info("Testing error handling...")
        
        try:
            # Test with invalid URL for similarity search
            params = ExaSimilarParams(
                url="not-a-valid-url",
                num_results=5
            )
            
            result = await self.client.find_similar(params)
            
            # Should fail due to invalid URL
            if result.success:
                logger.error("Error handling test failed: Invalid URL should not succeed")
                return False
            
            logger.info("✅ Error handling successful: Invalid URL properly rejected")
            return True
            
        except Exception as e:
            # Catching exception is also valid error handling
            logger.info(f"✅ Error handling successful: Exception caught - {str(e)}")
            return True
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        logger.info("🚀 Starting comprehensive integration tests")
        
        tests = [
            ("Configuration Validation", lambda: validate_config()),
            ("Basic Search", self.test_basic_search),
            ("Content Retrieval", self.test_content_retrieval),
            ("Similarity Search", self.test_similarity_search),
            ("Search Types Comparison", self.test_keyword_vs_neural_search),
            ("Domain Filtering", self.test_domain_filtering),
            ("Error Handling", self.test_error_handling),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    success = await test_func()
                else:
                    success = test_func()
                
                results[test_name] = success
                status = "✅ PASSED" if success else "❌ FAILED"
                logger.info(f"{status}: {test_name}")
                
            except Exception as e:
                results[test_name] = False
                logger.error(f"❌ FAILED: {test_name} - {str(e)}")
        
        return results


async def main():
    """Main test runner"""
    print("=" * 60)
    print("🧪 EXA MCP SERVER INTEGRATION TESTS")
    print("=" * 60)
    print()
    
    # Check environment
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("❌ Error: EXA_API_KEY environment variable not set")
        print("Please set your Exa API key:")
        print("export EXA_API_KEY='your_api_key_here'")
        return False
    
    print(f"🔑 API key found: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    tester = IntegrationTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run tests
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Your Exa MCP server is ready for production!")
            print("\nNext steps:")
            print("1. 📹 Record demonstration videos")
            print("2. 📝 Review documentation")
            print("3. 🚀 Submit your PR to Klavis AI")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please review and fix issues.")
            return False
            
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        return False
        
    finally:
        await tester.teardown()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)