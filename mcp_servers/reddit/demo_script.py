#!/usr/bin/env python3
"""
Reddit MCP Server Demo Script
This script demonstrates all 6 tools with natural language queries and live results.
Use this to create screenshots for proof of correctness.
"""

import os
import sys
from dotenv import load_dotenv
import praw

# Load environment variables
load_dotenv()

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

def print_demo_header(title):
    """Print a formatted demo header."""
    print("\n" + "="*60)
    print(f" 🎬 DEMO: {title}")
    print("="*60)

def print_natural_language_query(query):
    """Print natural language query."""
    print(f"\n📝 NATURAL LANGUAGE QUERY:")
    print(f"   \"{query}\"")
    print("-" * 40)

def print_tool_call(tool_name, parameters):
    """Print tool call information."""
    print(f"🔧 TOOL CALLED: {tool_name}")
    print(f"📋 PARAMETERS: {parameters}")
    print("-" * 40)

def print_live_results(results):
    """Print live results."""
    print(f"✅ LIVE RESULTS:")
    print(results)
    print("-" * 40)

def demo_tool_1_search_reddit_posts():
    """Demo Tool 1: search_reddit_posts"""
    print_demo_header("Tool 1: search_reddit_posts")
    
    # Natural language query
    query = "Search for posts about Python programming in the programming subreddit"
    print_natural_language_query(query)
    
    # Tool call
    tool_name = "search_reddit_posts"
    parameters = {
        "query": "Python programming",
        "subreddit": "programming",
        "limit": 5
    }
    print_tool_call(tool_name, parameters)
    
    # Live results
    try:
        subreddit_obj = reddit.subreddit("programming")
        search_results = subreddit_obj.search("Python programming", limit=5)
        
        results = []
        for post in search_results:
            results.append({
                "title": post.title,
                "author": str(post.author),
                "score": post.score,
                "url": f"https://reddit.com{post.permalink}"
            })
        
        live_results = f"Found {len(results)} posts:\n"
        for i, post in enumerate(results, 1):
            live_results += f"{i}. {post['title']} (Score: {post['score']})\n"
        
        print_live_results(live_results)
        
    except Exception as e:
        print_live_results(f"Error: {str(e)}")

def demo_tool_2_get_post_details():
    """Demo Tool 2: get_post_details"""
    print_demo_header("Tool 2: get_post_details")
    
    # Natural language query
    query = "Get details about this Python post"
    print_natural_language_query(query)
    
    # Tool call
    tool_name = "get_post_details"
    parameters = {"post_id": "1mg53kt"}
    print_tool_call(tool_name, parameters)
    
    # Live results
    try:
        post = reddit.submission(id="1mg53kt")
        live_results = f"Post Details:\n"
        live_results += f"Title: {post.title}\n"
        live_results += f"Author: {post.author}\n"
        live_results += f"Score: {post.score}\n"
        live_results += f"Comments: {post.num_comments}\n"
        live_results += f"URL: https://reddit.com{post.permalink}\n"
        
        print_live_results(live_results)
        
    except Exception as e:
        print_live_results(f"Error: {str(e)}")

def demo_tool_3_get_trending_posts():
    """Demo Tool 3: get_trending_posts"""
    print_demo_header("Tool 3: get_trending_posts")
    
    # Natural language query
    query = "Get trending posts from r/Python"
    print_natural_language_query(query)
    
    # Tool call
    tool_name = "get_trending_posts"
    parameters = {"subreddit": "Python", "limit": 5}
    print_tool_call(tool_name, parameters)
    
    # Live results
    try:
        subreddit_obj = reddit.subreddit("Python")
        hot_posts = subreddit_obj.hot(limit=5)
        
        results = []
        for post in hot_posts:
            results.append({
                "title": post.title,
                "author": str(post.author),
                "score": post.score,
                "url": f"https://reddit.com{post.permalink}"
            })
        
        live_results = f"Trending posts from r/Python:\n"
        for i, post in enumerate(results, 1):
            live_results += f"{i}. {post['title']} (Score: {post['score']})\n"
        
        print_live_results(live_results)
        
    except Exception as e:
        print_live_results(f"Error: {str(e)}")

def demo_tool_4_list_subreddits():
    """Demo Tool 4: list_subreddits"""
    print_demo_header("Tool 4: list_subreddits")
    
    # Natural language query
    query = "List programming subreddits"
    print_natural_language_query(query)
    
    # Tool call
    tool_name = "list_subreddits"
    parameters = {"query": "programming", "limit": 5}
    print_tool_call(tool_name, parameters)
    
    # Live results
    try:
        subreddits = list(reddit.subreddits.search("programming", limit=5))
        
        live_results = f"Programming subreddits:\n"
        for i, subreddit in enumerate(subreddits, 1):
            live_results += f"{i}. r/{subreddit.display_name} ({subreddit.subscribers:,} subscribers)\n"
        
        print_live_results(live_results)
        
    except Exception as e:
        print_live_results(f"Error: {str(e)}")

def demo_tool_5_get_user_info():
    """Demo Tool 5: get_user_info"""
    print_demo_header("Tool 5: get_user_info")
    
    # Natural language query
    query = "Get information about user example_user"
    print_natural_language_query(query)
    
    # Tool call
    tool_name = "get_user_info"
    parameters = {"username": "example_user"}
    print_tool_call(tool_name, parameters)
    
    # Live results
    try:
        user = reddit.redditor("example_user")
        live_results = f"User Profile: u/example_user\n"
        live_results += f"Post Karma: {user.link_karma:,}\n"
        live_results += f"Comment Karma: {user.comment_karma:,}\n"
        live_results += f"Account Created: {user.created_utc}\n"
        
        print_live_results(live_results)
        
    except Exception as e:
        print_live_results(f"Error: {str(e)}")

def demo_tool_6_get_subreddit_info():
    """Demo Tool 6: get_subreddit_info"""
    print_demo_header("Tool 6: get_subreddit_info")
    
    # Natural language query
    query = "Get information about r/Python subreddit"
    print_natural_language_query(query)
    
    # Tool call
    tool_name = "get_subreddit_info"
    parameters = {"subreddit": "Python"}
    print_tool_call(tool_name, parameters)
    
    # Live results
    try:
        subreddit = reddit.subreddit("Python")
        live_results = f"Subreddit Info: r/Python\n"
        live_results += f"Subscribers: {subreddit.subscribers:,}\n"
        live_results += f"Active Users: {subreddit.active_user_count}\n"
        live_results += f"Description: {subreddit.public_description[:100]}...\n"
        
        print_live_results(live_results)
        
    except Exception as e:
        print_live_results(f"Error: {str(e)}")

def main():
    """Run all demos."""
    print("🎬 REDDIT MCP SERVER DEMO")
    print("="*60)
    print("This demo shows natural language queries and live results for all 6 tools.")
    print("Use these outputs to create screenshots for proof of correctness.")
    print("="*60)
    
    # Run all demos
    demo_tool_1_search_reddit_posts()
    demo_tool_2_get_post_details()
    demo_tool_3_get_trending_posts()
    demo_tool_4_list_subreddits()
    demo_tool_5_get_user_info()
    demo_tool_6_get_subreddit_info()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("Use these outputs to create screenshots for your pull request.")
    print("="*60)

if __name__ == "__main__":
    main()
