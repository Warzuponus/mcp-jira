# MCP JIRA Server

A Model Context Protocol (MCP) server that enables Language Models to interact with JIRA. This server provides a standardized interface for AI applications to manage JIRA issues, workflows, and tasks through the MCP specification.

[![NPM version](https://img.shields.io/npm/v/@modelcontextprotocol/server-jira.svg)](https://www.npmjs.com/package/@modelcontextprotocol/server-jira)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **JIRA Issue Management**
  - Create new issues
  - Update existing issues
  - Search issues using JQL
  - Track issue status changes

- **MCP Integration**
  - Tools for JIRA operations
  - Resource templates for issue access
  - Real-time updates via SSE
  - Pagination support

## Installation

```bash
npm install @modelcontextprotocol/server-jira
```

## Configuration

### Environment Variables

```env
JIRA_PROTOCOL=https
JIRA_HOST=your-instance.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_API_VERSION=2
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-jira"
      ],
      "env": {
        "JIRA_PROTOCOL": "https",
        "JIRA_HOST": "your-instance.atlassian.net",
        "JIRA_USERNAME": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token",
        "JIRA_API_VERSION": "2"
      }
    }
  }
}
```

## API Reference

### Tools

1. `createIssue`
   - Creates a new JIRA issue
   - Parameters:
     - `project` (string): Project key
     - `summary` (string): Issue summary
     - `description` (string): Issue description
     - `issueType` (string): Type of issue

2. `updateIssue`
   - Updates an existing issue
   - Parameters:
     - `issueKey` (string): Key of the issue to update
     - `summary` (string, optional): New summary
     - `description` (string, optional): New description
     - `status` (string, optional): New status

3. `searchIssues`
   - Searches for issues using JQL
   - Parameters:
     - `jql` (string): JQL query string
     - `maxResults` (number, optional): Maximum results to return

### Resources

Access issue details using the resource template:
```
jira://issue/{issueKey}
```

Example:
```
jira://issue/PROJ-123
```

## Development

### Prerequisites

- Node.js 18+
- npm or yarn
- JIRA account with API access

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Warzuponus/mcp-jira.git
   cd mcp-jira
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the project:
   ```bash
   npm run build
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

### Testing

```bash
npm test
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## Security

For security concerns, please see our [Security Policy](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [jira-client](https://github.com/jira-client/jira-client) for JIRA API integration