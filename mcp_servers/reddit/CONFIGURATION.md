# Configuration Guide

## Setting Up Reddit API Credentials

### Step 1: Create a Reddit Application

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the application details:
   - **Name**: Your app name (e.g., "MCP Reddit Server")
   - **App type**: Select "script"
   - **Description**: Brief description of your app
   - **About URL**: Can be left blank
   - **Redirect URI**: Use `http://localhost:8080` (not actually used for script apps)
4. Click "Create App"

### Step 2: Get Your Credentials

After creating the app, you'll see:
- **Client ID**: The string under your app name (this is your Client ID)
- **Client Secret**: The "secret" field (this is your Client Secret)

### Step 3: Configure Environment Variables

Create a `.env` file in the project root with the following content:

```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MCP_Reddit_Server/1.0 (by /u/your_username)
```

Replace the placeholder values with your actual credentials.

### Step 4: Verify Configuration

Run the test script to verify your configuration:

```bash
python test_reddit_server.py
```

You should see "✅ Reddit API credentials found!" if everything is configured correctly.

## Security Notes

- **Never commit your .env file to version control**
- **Keep your Client Secret secure**
- **The server only makes read-only requests to Reddit's API**
- **No user authentication is required for public data access**

## Troubleshooting

### Common Issues

1. **"Reddit API credentials not configured"**
   - Make sure you've created a `.env` file
   - Verify the environment variable names are correct
   - Check that the values are not empty

2. **"Failed to initialize Reddit client"**
   - Verify your Client ID and Client Secret are correct
   - Check that you selected "script" as the app type
   - Ensure your Reddit account is in good standing

3. **Rate limiting errors**
   - Reddit's API has rate limits (60 requests per minute)
   - The server handles this automatically, but you may need to wait

### Getting Help

If you encounter issues:
1. Check the Reddit API documentation: https://www.reddit.com/dev/api/
2. Verify your app settings at https://www.reddit.com/prefs/apps
3. Test with a simple Reddit API call first 