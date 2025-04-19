# Slack Bot Setup Guide

This guide will help you set up your own Slack app and connect it to our application.

## Prerequisites

- A Slack workspace where you have admin permissions
- Python 3.12+ installed on your machine
- uv 0.6.14+ installed on your machine
- Git repository cloned locally
- ngrok installed (for local development)

## Step 1: Environment Setup

1. Copy the example environment file to create your own:
   ```bash
   cp .env.example .env
   ```

## Step 2: Create a Slack App

1. Visit the [Slack API Apps page](https://api.slack.com/apps) and click "Create New App"
2. Choose "From scratch" and provide:
   - App Name: (your choice)
   - Development Slack Workspace: (your workspace)
3. From the "Basic Information" page, update these values in your `.env` file:
   - `APP_ID`
   - `CLIENT_ID`
   - `CLIENT_SECRET`
   - `SIGNING_SECRET`

## Step 3: Configure OAuth & Permissions

1. Go to "OAuth & Permissions" in your app settings
2. Under "Bot Token Scopes", add the following scopes:
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `files:read`
   - `im:write`
   - `reactions:read`
   - `reactions:write`

## Step 4: Start Local Development Environment

1. Run your application (default port is 8080):
   ```bash
   uv run slack_bot
   ```
2. Start ngrok to create a secure tunnel to your local server:
   ```bash
   ngrok http 8080
   ```
3. Copy the HTTPS URL provided by ngrok (e.g., `https://7c2b-2601-645-8400-6db0-c0b0-639c-bb9d-5d8c.ngrok-free.app`)

## Step 5: Configure Event Subscriptions

1. Go to "Event Subscriptions" and toggle "Enable Events" to ON
2. Set the Request URL to `https://[your-ngrok-url]/slack/events`
   - Slack will send a challenge request to verify your URL
   - Your running application will automatically respond to this challenge
3. Under "Subscribe to bot events", add:
   - `app_mention` (for detecting when your bot is mentioned)
   - `message.im` (for direct messages to your bot)
4. Save your changes

## Step 6: Install Your App

1. Navigate to the "Install App" section
2. Click "Install to Workspace"
3. Review and authorize the permissions requested

## Step 7: Get Your Bot User ID

After installing your app, you need to get the Bot User ID:

1. Use the Slack API:
   ```bash
   curl -H "Authorization: Bearer xoxb-your-bot-token" https://slack.com/api/auth.test
   ```
   The response includes a `user_id` field - that's your `SLACK_BOT_USER_ID`

2. Update your `.env` file with the Bot User ID

## Step 8: Test Your Bot

1. In Slack, send a direct message to your bot
2. Tag your bot in a channel where it's been added: `@yourbot hello`
3. Verify that your application receives and processes these messages
