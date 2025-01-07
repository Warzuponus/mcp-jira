#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Retrieve environment variables
const JIRA_INSTANCE_URL = process.env.JIRA_INSTANCE_URL;
const JIRA_API_KEY = process.env.JIRA_API_KEY;
const JIRA_USER_EMAIL = process.env.JIRA_USER_EMAIL;

// Validate environment variables
if (!JIRA_INSTANCE_URL || !JIRA_API_KEY || !JIRA_USER_EMAIL) {
  console.error(
    "Error: JIRA_INSTANCE_URL, JIRA_USER_EMAIL, and JIRA_API_KEY must be set in the environment."
  );
  process.exit(1);
}

// Initialize the server
const server = new Server(
  {
    name: "jira-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define tools for backlog management
server.setRequestHandler("listTools", async () => {
  return {
    tools: [
      {
        name: "search_backlog",
        description: "Search issues in the backlog",
        inputSchema: {
          type: "object",
          properties: {
            projectKey: { type: "string", description: "Project key (e.g., 'PROJ')" },
            searchTerm: { type: "string", description: "Optional search term" }
          },
          required: ["projectKey"]
        }
      },
      {
        name: "update_issue",
        description: "Update an issue's priority, status, or assignee",
        inputSchema: {
          type: "object",
          properties: {
            issueKey: { type: "string", description: "Issue key (e.g., 'PROJ-123')" },
            priority: { type: "string", description: "Priority level" },
            status: { type: "string", description: "New status" },
            assignee: { type: "string", description: "Username to assign to" }
          },
          required: ["issueKey"]
        }
      },
      {
        name: "create_issue",
        description: "Create a new issue in the backlog",
        inputSchema: {
          type: "object",
          properties: {
            projectKey: { type: "string", description: "Project key" },
            summary: { type: "string", description: "Issue summary" },
            description: { type: "string", description: "Issue description" },
            issueType: { type: "string", description: "Type of issue" },
            priority: { type: "string", description: "Priority level" }
          },
          required: ["projectKey", "summary", "issueType"]
        }
      }
    ]
  };
});

// Handle tool execution
server.setRequestHandler("callTool", async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const auth = Buffer.from(`${JIRA_USER_EMAIL}:${JIRA_API_KEY}`).toString("base64");

    switch (name) {
      case "search_backlog": {
        const response = await fetch(
          `${JIRA_INSTANCE_URL}/rest/api/2/search`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Basic ${auth}`,
            },
            body: JSON.stringify({
              jql: `project = ${args.projectKey} AND status = Backlog ${args.searchTerm ? `AND text ~ "${args.searchTerm}"` : ''}`,
              maxResults: 50
            }),
          }
        );

        if (!response.ok) throw new Error(`JIRA API Error: ${response.statusText}`);
        const data = await response.json();
        return { type: "text", content: JSON.stringify(data, null, 2) };
      }

      case "update_issue": {
        const updateData = {
          fields: {}
        };

        if (args.priority) updateData.fields.priority = { name: args.priority };
        if (args.status) updateData.fields.status = { name: args.status };
        if (args.assignee) updateData.fields.assignee = { name: args.assignee };

        const response = await fetch(
          `${JIRA_INSTANCE_URL}/rest/api/2/issue/${args.issueKey}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Basic ${auth}`,
            },
            body: JSON.stringify(updateData),
          }
        );

        if (!response.ok) throw new Error(`JIRA API Error: ${response.statusText}`);
        return { type: "text", content: `Updated issue ${args.issueKey}` };
      }

      case "create_issue": {
        const response = await fetch(
          `${JIRA_INSTANCE_URL}/rest/api/2/issue`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Basic ${auth}`,
            },
            body: JSON.stringify({
              fields: {
                project: { key: args.projectKey },
                summary: args.summary,
                description: args.description,
                issuetype: { name: args.issueType },
                priority: args.priority ? { name: args.priority } : undefined
              }
            }),
          }
        );

        if (!response.ok) throw new Error(`JIRA API Error: ${response.statusText}`);
        const data = await response.json();
        return { type: "text", content: `Created issue ${data.key}` };
      }
    }
  } catch (error) {
    return { isError: true, content: error.message };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log("JIRA MCP Server is running.");
}

main().catch((error) => {
  console.error("Error starting the server:", error);
});