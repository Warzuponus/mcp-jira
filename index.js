#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";

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

// Define tools for comprehensive project management
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "analyze_sprint",
        description: "Analyze current sprint status, progress, and potential blockers",
        inputSchema: {
          type: "object",
          properties: {
            projectKey: { type: "string", description: "Project key (e.g., 'PROJ')" },
            sprintId: { type: "string", description: "Optional: Specific sprint ID" }
          },
          required: ["projectKey"]
        }
      },
      {
        name: "plan_sprint",
        description: "Plan a new sprint including capacity planning and issue selection",
        inputSchema: {
          type: "object",
          properties: {
            projectKey: { type: "string", description: "Project key" },
            teamCapacity: { type: "number", description: "Team capacity in story points" },
            startDate: { type: "string", description: "Sprint start date (YYYY-MM-DD)" },
            endDate: { type: "string", description: "Sprint end date (YYYY-MM-DD)" },
            sprintGoals: { type: "string", description: "Goals for the sprint" }
          },
          required: ["projectKey", "teamCapacity", "startDate", "endDate"]
        }
      },
      {
        name: "create_issue",
        description: "Create a new issue with detailed attributes",
        inputSchema: {
          type: "object",
          properties: {
            projectKey: { type: "string", description: "Project key" },
            summary: { type: "string", description: "Issue summary" },
            description: { type: "string", description: "Issue description" },
            issueType: { type: "string", description: "Type of issue" },
            priority: { type: "string", description: "Priority level" },
            storyPoints: { type: "number", description: "Story points estimate" },
            assignee: { type: "string", description: "Assignee username" },
            dueDate: { type: "string", description: "Due date (YYYY-MM-DD)" },
            epic: { type: "string", description: "Epic link" }
          },
          required: ["projectKey", "summary", "issueType"]
        }
      },
      {
        name: "update_issue",
        description: "Update issue details including story points and status",
        inputSchema: {
          type: "object",
          properties: {
            issueKey: { type: "string", description: "Issue key (e.g., 'PROJ-123')" },
            storyPoints: { type: "number", description: "Story points estimate" },
            priority: { type: "string", description: "Priority level" },
            status: { type: "string", description: "New status" },
            assignee: { type: "string", description: "Username to assign to" },
            dueDate: { type: "string", description: "Due date (YYYY-MM-DD)" }
          },
          required: ["issueKey"]
        }
      },
      {
        name: "generate_report",
        description: "Generate sprint/project progress report",
        inputSchema: {
          type: "object",
          properties: {
            projectKey: { type: "string", description: "Project key" },
            reportType: { 
              type: "string", 
              enum: ["sprint_progress", "velocity", "backlog_health", "team_workload"],
              description: "Type of report to generate"
            },
            timeFrame: { type: "string", description: "Time frame for the report (e.g., 'last_sprint', 'last_month')" }
          },
          required: ["projectKey", "reportType"]
        }
      }
    ]
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const auth = Buffer.from(`${JIRA_USER_EMAIL}:${JIRA_API_KEY}`).toString("base64");
    const headers = {
      "Content-Type": "application/json",
      Authorization: `Basic ${auth}`,
    };

    switch (name) {
      case "analyze_sprint": {
        // Get active sprint
        const sprintResponse = await fetch(
          `${JIRA_INSTANCE_URL}/rest/agile/1.0/board/search?projectKeyOrId=${args.projectKey}`,
          { headers }
        );
        const boards = await sprintResponse.json();
        const boardId = boards.values[0].id;

        const activeSprint = await fetch(
          `${JIRA_INSTANCE_URL}/rest/agile/1.0/board/${boardId}/sprint?state=active`,
          { headers }
        );
        const sprintData = await activeSprint.json();
        const sprint = sprintData.values[0];

        // Get sprint issues
        const issuesResponse = await fetch(
          `${JIRA_INSTANCE_URL}/rest/agile/1.0/sprint/${sprint.id}/issue`,
          { headers }
        );
        const issues = await issuesResponse.json();

        // Analyze sprint health
        const analysis = analyzeSprintHealth(issues.issues, sprint);

        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              sprint: sprint,
              analysis: analysis
            }, null, 2)
          }]
        };
      }

      case "plan_sprint": {
        // Get backlog issues
        const response = await fetch(
          `${JIRA_INSTANCE_URL}/rest/api/2/search`,
          {
            method: "POST",
            headers,
            body: JSON.stringify({
              jql: `project = ${args.projectKey} AND status = Backlog ORDER BY priority DESC, created ASC`,
              maxResults: 100
            }),
          }
        );

        const data = await response.json();
        const plannedIssues = selectIssuesForSprint(data.issues, args.teamCapacity);

        // Create new sprint
        const createSprintResponse = await fetch(
          `${JIRA_INSTANCE_URL}/rest/agile/1.0/sprint`,
          {
            method: "POST",
            headers,
            body: JSON.stringify({
              name: `Sprint starting ${args.startDate}`,
              startDate: args.startDate,
              endDate: args.endDate,
              originBoardId: boardId,
              goal: args.sprintGoals
            }),
          }
        );

        const sprint = await createSprintResponse.json();

        // Move issues to sprint
        await fetch(
          `${JIRA_INSTANCE_URL}/rest/agile/1.0/sprint/${sprint.id}/issue`,
          {
            method: "POST",
            headers,
            body: JSON.stringify({
              issues: plannedIssues.map(issue => issue.key)
            }),
          }
        );

        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify({
              sprint: sprint,
              plannedIssues: plannedIssues,
              totalStoryPoints: plannedIssues.reduce((sum, issue) => sum + (issue.fields.customfield_10016 || 0), 0)
            }, null, 2)
          }]
        };
      }

      case "generate_report": {
        const reportData = await generateReport(args.projectKey, args.reportType, args.timeFrame, JIRA_INSTANCE_URL, headers);
        return { 
          content: [{ 
            type: "text", 
            text: JSON.stringify(reportData, null, 2)
          }]
        };
      }

      // ... existing create_issue and update_issue handlers ...
    }
  } catch (error) {
    return { 
      isError: true, 
      content: [{ 
        type: "text", 
        text: error.message 
      }]
    };
  }
});

// Helper functions
function analyzeSprintHealth(issues, sprint) {
  const analysis = {
    totalIssues: issues.length,
    completed: 0,
    inProgress: 0,
    blocked: 0,
    storyPoints: {
      total: 0,
      completed: 0
    },
    risksAndBlockers: []
  };

  issues.forEach(issue => {
    const status = issue.fields.status.name.toLowerCase();
    const storyPoints = issue.fields.customfield_10016 || 0;

    analysis.storyPoints.total += storyPoints;

    if (status === 'done') {
      analysis.completed++;
      analysis.storyPoints.completed += storyPoints;
    } else if (status === 'in progress') {
      analysis.inProgress++;
    }

    // Check for blockers
    if (issue.fields.flagged || issue.fields.priority.name === 'Highest') {
      analysis.blocked++;
      analysis.risksAndBlockers.push({
        key: issue.key,
        summary: issue.fields.summary,
        priority: issue.fields.priority.name
      });
    }
  });

  return analysis;
}

function selectIssuesForSprint(issues, capacity) {
  const plannedIssues = [];
  let totalPoints = 0;

  for (const issue of issues) {
    const storyPoints = issue.fields.customfield_10016 || 0;
    if (totalPoints + storyPoints <= capacity) {
      plannedIssues.push(issue);
      totalPoints += storyPoints;
    }
  }

  return plannedIssues;
}

async function generateReport(projectKey, reportType, timeFrame, jiraUrl, headers) {
  // Implementation varies based on report type
  switch (reportType) {
    case 'sprint_progress':
      // Fetch current sprint data
      break;
    case 'velocity':
      // Calculate velocity over last few sprints
      break;
    case 'backlog_health':
      // Analyze backlog items
      break;
    case 'team_workload':
      // Calculate team member workload
      break;
  }

  return {
    type: reportType,
    timeFrame: timeFrame,
    // ... report specific data
  };
}

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.log("JIRA MCP Server is running.");
}

main().catch((error) => {
  console.error("Error starting the server:", error);
});
