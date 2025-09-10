# Quick Start Guide

Get your MCP Jira server running in 5 minutes!

## Prerequisites

- Python 3.8+
- Jira account with API access
- Claude Desktop or another MCP client

## Step 1: Install

```bash
cd mcp-jira
pip install -e .
```

## Step 2: Configure

Create a `.env` file:

```bash
# Copy the example
cp .env.example .env

# Edit with your details
nano .env
```

Required settings:
```env
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_api_token_here
PROJECT_KEY=PROJ
```

## Step 3: Get Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token to your `.env` file

## Step 4: Test the Server

```bash
python -m mcp_jira
```

You should see: `🚀 Starting MCP Jira Server...`

## Step 5: Connect to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-jira": {
      "command": "python",
      "args": ["-m", "mcp_jira"],
      "cwd": "/path/to/mcp-jira"
    }
  }
}
```

## Step 6: Try It Out!

In Claude Desktop, try:

- "Create a high priority bug for login issues"
- "What's our current sprint status?"
- "Show me all issues assigned to john.doe"
- "Generate today's standup report"

## Troubleshooting

### "No .env file found"
- Make sure you created `.env` in the project root
- Copy from `.env.example` if available

### "Authentication failed"
- Check your API token is correct
- Verify your username is your email address
- Ensure the Jira URL is correct

### "No active sprint found"
- Make sure your board has an active sprint
- Set `DEFAULT_BOARD_ID` in your `.env`

### "Permission denied"
- Verify your Jira user has project access
- Check the `PROJECT_KEY` is correct

## Next Steps

- Explore all available tools with "What tools do you have?"
- Set up team workload monitoring
- Automate your daily standups
- Create custom JQL searches

Happy project managing! 🎯 