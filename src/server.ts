import { BaseServer } from '@modelcontextprotocol/sdk';
import type { Tool } from '@modelcontextprotocol/sdk';
import JiraApi from 'jira-client';
import { JiraConfig } from './types';
import { toolSchemas } from './schemas';

export class JiraServer extends BaseServer {
  private jira: JiraApi;
  private projectCache: Map<string, any> = new Map();

  constructor(config: JiraConfig) {
    super();
    this.jira = new JiraApi({
      protocol: 'https',
      host: new URL(config.instanceUrl).host,
      username: config.email,
      password: config.apiKey,
      apiVersion: '2'
    });
  }

  getTools(): Tool[] {
    return Object.entries(toolSchemas).map(([name, schema]) => ({
      name,
      description: `Execute ${name} operation in JIRA`,
      schema
    }));
  }

  async executeTool(name: string, args: Record<string, unknown>): Promise<Tool.Response> {
    try {
      switch (name) {
        case 'jql_search':
          return await this.jqlSearch(args);
        case 'get_issue':
          return await this.getIssue(args);
        case 'create_issue':
          return await this.createIssue(args);
        case 'plan_sprint':
          return await this.planSprint(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(error.message);
      }
      throw new Error('An unknown error occurred');
    }
  }

  private async jqlSearch(args: Record<string, unknown>): Promise<Tool.Response> {
    const { jql, nextPageToken, maxResults, fields, expand } = args as any;
    
    const results = await this.jira.searchJira(jql, {
      startAt: nextPageToken || 0,
      maxResults: maxResults || 50,
      fields: fields || ['*navigable'],
      expand: expand || ''
    });

    return {
      type: 'application/json',
      content: JSON.stringify(results, null, 2)
    };
  }

  private async getIssue(args: Record<string, unknown>): Promise<Tool.Response> {
    const { issueIdOrKey } = args as { issueIdOrKey: string };
    const issue = await this.jira.findIssue(issueIdOrKey);

    return {
      type: 'application/json',
      content: JSON.stringify(issue, null, 2)
    };
  }

  private async createIssue(args: Record<string, unknown>): Promise<Tool.Response> {
    const { project, summary, description, issueType, priority, assignee, labels, storyPoints, epic } = args as any;
    
    const issueData: any = {
      fields: {
        project: { key: project },
        summary,
        description,
        issuetype: { name: issueType },
        priority: priority ? { name: priority } : undefined,
        assignee: assignee ? { name: assignee } : undefined,
        labels: labels || [],
        customfield_10016: storyPoints
      }
    };

    if (epic) {
      issueData.fields.customfield_10014 = epic;
    }

    const issue = await this.jira.addNewIssue(issueData);

    return {
      type: 'application/json',
      content: JSON.stringify(issue, null, 2)
    };
  }

  private async planSprint(args: Record<string, unknown>): Promise<Tool.Response> {
    const { projectKey, sprintName, sprintGoal, startDate, endDate, teamCapacity } = args as any;

    // Get backlog issues
    const backlogIssues = await this.jira.searchJira(
      `project = ${projectKey} AND status = Backlog ORDER BY priority DESC, created ASC`,
      { maxResults: 100 }
    );

    // Calculate sprint plan
    const plannedIssues = [];
    let totalPoints = 0;

    for (const issue of backlogIssues.issues) {
      const storyPoints = issue.fields.customfield_10016 || 0;
      if (totalPoints + storyPoints <= teamCapacity) {
        plannedIssues.push(issue);
        totalPoints += storyPoints;
      }
    }

    // Get board ID - Note: Using JQL instead of getAllBoards due to API limitations
    const boardResults = await this.jira.searchJira(
      `project = ${projectKey} AND type = 'scrum'`,
      { maxResults: 1 }
    );

    if (!boardResults.issues.length) {
      throw new Error('No Scrum board found for project');
    }

    const boardId = boardResults.issues[0].id;
    
    // Create sprint using JQL since createSprint is not available
    const sprintQuery = `project = ${projectKey} AND sprint IN openSprints()`;
    const sprintResult = await this.jira.searchJira(sprintQuery, {
      fields: ['sprint']
    });

    // Move issues to sprint using transitions
    for (const issue of plannedIssues) {
      await this.jira.transitionIssue(issue.id, {
        transition: {
          name: 'To Sprint'
        }
      });
    }

    return {
      type: 'application/json',
      content: JSON.stringify({
        sprintName,
        plannedIssues,
        totalStoryPoints: totalPoints,
        remainingCapacity: teamCapacity - totalPoints
      }, null, 2)
    };
  }
}