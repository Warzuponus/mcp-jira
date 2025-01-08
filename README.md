# JIRA Project Management Assistant (MCP)

A Model Context Protocol (MCP) server that enables Claude to act as a Scrum Master and Executive Assistant for engineering managers. This server provides comprehensive capabilities for sprint planning, backlog management, and project analytics.

## Features

### Sprint Management
- Analyze current sprint progress and health
- Plan new sprints with capacity planning
- Track velocity and team performance
- Identify and manage blockers

### Backlog Management
- Create and update issues
- Manage story points and priorities
- Track due dates and assignments
- Link issues to epics

### Analytics and Reporting
- Generate sprint progress reports
- Analyze team velocity
- Assess backlog health
- Monitor team workload
- Track completion rates

## Prerequisites

- Node.js v18 or higher
- JIRA instance with API access
- JIRA API token

## Installation

```bash
# Clone the repository
git clone https://github.com/Warzuponus/mcp-jira.git
cd mcp-jira

# Install dependencies
npm install
```

## Configuration

1. **Get JIRA API Token**:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Create an API token
   - Note down:
     - Your JIRA instance URL
     - Your email
     - The API token

2. **Configure Claude Desktop**:

Edit your configuration file:
- macOS: `~/Library/Application Support/Claude Desktop/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude Desktop\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jira": {
      "command": "/opt/homebrew/bin/node",
      "args": ["/absolute/path/to/mcp-jira/index.js"],
      "env": {
        "JIRA_INSTANCE_URL": "https://your-instance.atlassian.net",
        "JIRA_USER_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Example Usage

### Sprint Management
```
"How is our current sprint in PROJECT progressing?"
"Plan the next sprint for PROJECT with a capacity of 40 story points"
"What are the current blockers in our sprint?"
"Show me the velocity trend for the last 3 sprints"
```

### Backlog Management
```
"Create a new high-priority task in PROJECT for implementing OAuth"
"Update PROJECT-123 to 5 story points and assign it to john.doe"
"Show me all unestimated stories in the PROJECT backlog"
"What's the current distribution of story points across the team?"
```

### Reports and Analytics
```
"Generate a sprint progress report for PROJECT"
"Show me the team's velocity over the last quarter"
"Analyze the health of PROJECT's backlog"
"What's the current workload distribution across the team?"
```

## Development

### Running Locally
```bash
# Set environment variables
export JIRA_INSTANCE_URL="https://your-instance.atlassian.net"
export JIRA_USER_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"

# Run the server
node index.js
```

### Available Tools

1. `analyze_sprint`
   - Analyzes current sprint status and health
   - Identifies blockers and risks
   - Tracks completion rates

2. `plan_sprint`
   - Plans new sprints based on team capacity
   - Selects appropriate issues from backlog
   - Sets sprint goals and dates

3. `create_issue`
   - Creates new JIRA issues with full details
   - Supports story points, priority, and assignments
   - Links to epics

4. `update_issue`
   - Updates existing issues
   - Modifies story points, status, and assignments
   - Sets due dates

5. `generate_report`
   - Creates various project reports
   - Analyzes sprint progress
   - Tracks team performance

## Troubleshooting

### Common Issues

1. **Connection Issues**
   - Verify JIRA API token is correct
   - Check instance URL format
   - Ensure network access to JIRA

2. **Permission Issues**
   - Verify user has required JIRA permissions
   - Check project access rights
   - Validate API token scope

3. **Sprint Planning Issues**
   - Ensure project has an active board
   - Verify sprint dates are valid
   - Check team capacity settings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Areas for improvement:

- Additional report types
- Enhanced sprint analytics
- Team performance metrics
- Custom field support
- Board configuration management

## License

MIT
