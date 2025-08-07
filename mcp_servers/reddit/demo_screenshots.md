# Demo Screenshots Guide for Reddit MCP Server

## 📸 **Required Screenshots for Proof of Correctness**

### **Tool 1: search_reddit_posts**

**Screenshot 1: Natural Language Query**
- Open Cursor or any MCP client
- Type: "Search for posts about Python programming in the programming subreddit"
- Screenshot showing the query

**Screenshot 2: Tool Call**
- Show the MCP tool being called: `search_reddit_posts`
- Parameters: `query='Python programming', subreddit='programming', limit=5`

**Screenshot 3: Live Results**
- Show the actual Reddit API response with real posts
- Example output from our live testing

### **Tool 2: get_post_details**

**Screenshot 1: Natural Language Query**
- Query: "Get details about this Python post"

**Screenshot 2: Tool Call**
- Tool: `get_post_details`
- Parameters: `post_id='1mg53kt'`

**Screenshot 3: Live Results**
- Show complete post details with comments

### **Tool 3: get_trending_posts**

**Screenshot 1: Natural Language Query**
- Query: "Get trending posts from r/Python"

**Screenshot 2: Tool Call**
- Tool: `get_trending_posts`
- Parameters: `subreddit='Python', limit=5`

**Screenshot 3: Live Results**
- Show current trending posts from r/Python

### **Tool 4: list_subreddits**

**Screenshot 1: Natural Language Query**
- Query: "List programming subreddits"

**Screenshot 2: Tool Call**
- Tool: `list_subreddits`
- Parameters: `query='programming', limit=5`

**Screenshot 3: Live Results**
- Show list of programming subreddits with subscriber counts

### **Tool 5: get_user_info**

**Screenshot 1: Natural Language Query**
- Query: "Get information about user example_user"

**Screenshot 2: Tool Call**
- Tool: `get_user_info`
- Parameters: `username='example_user'`

**Screenshot 3: Live Results**
- Show user profile information

### **Tool 6: get_subreddit_info**

**Screenshot 1: Natural Language Query**
- Query: "Get information about r/Python subreddit"

**Screenshot 2: Tool Call**
- Tool: `get_subreddit_info`
- Parameters: `subreddit='Python'`

**Screenshot 3: Live Results**
- Show subreddit metadata and statistics

## 🎬 **Alternative: Video Recording**

If screenshots are difficult, create a 2-3 minute video showing:

1. **Introduction** (10 seconds)
   - "This is a demonstration of the Reddit MCP Server"

2. **Tool 1 Demo** (30 seconds)
   - Show natural language query
   - Show tool call
   - Show live results

3. **Tool 2 Demo** (30 seconds)
   - Repeat for second tool

4. **Continue for all 6 tools** (2-3 minutes total)

## 📋 **Screenshot Checklist**

- [ ] Tool 1: search_reddit_posts (3 screenshots)
- [ ] Tool 2: get_post_details (3 screenshots)
- [ ] Tool 3: get_trending_posts (3 screenshots)
- [ ] Tool 4: list_subreddits (3 screenshots)
- [ ] Tool 5: get_user_info (3 screenshots)
- [ ] Tool 6: get_subreddit_info (3 screenshots)

**Total: 18 screenshots or 1 video covering all 6 tools**

## 🚀 **How to Capture**

1. **Use screen recording software** (QuickTime, OBS, etc.)
2. **Take screenshots** of each step
3. **Organize by tool** in a folder
4. **Upload to the PR** as attachments

This will provide the required visual proof of functionality!
