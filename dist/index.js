#!/usr/bin/env node
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const sdk_1 = require("@modelcontextprotocol/sdk");
const server_1 = require("./server");
// Validate environment variables
const JIRA_INSTANCE_URL = process.env.JIRA_INSTANCE_URL;
const JIRA_API_KEY = process.env.JIRA_API_KEY;
const JIRA_USER_EMAIL = process.env.JIRA_USER_EMAIL;
if (!JIRA_INSTANCE_URL || !JIRA_API_KEY || !JIRA_USER_EMAIL) {
    console.error('Error: JIRA_INSTANCE_URL, JIRA_USER_EMAIL, and JIRA_API_KEY must be set in the environment.');
    process.exit(1);
}
// Initialize the server
const server = new sdk_1.Server({
    name: 'jira-mcp',
    version: '1.0.0',
}, {
    capabilities: {
        tools: {},
    },
});
// Initialize JIRA server with our enhanced functionality
const jiraServer = new server_1.JiraServer({
    instanceUrl: JIRA_INSTANCE_URL,
    email: JIRA_USER_EMAIL,
    apiKey: JIRA_API_KEY
});
// Register tools and start server
async function main() {
    const transport = new sdk_1.StdioServerTransport();
    await server.connect(transport);
    // Register server capabilities
    server.setTools(jiraServer.getTools());
    console.log('JIRA MCP Server is running.');
}
main().catch((error) => {
    console.error('Error starting the server:', error);
    process.exit(1);
});
