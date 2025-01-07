import { BaseServer } from '@modelcontextprotocol/sdk';
import { Tool, Resource, ResourceTemplate, ToolError } from '@modelcontextprotocol/sdk';
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
      host: config.instanceUrl.replace('https://', ''),
      username: config.email,
      password: config.apiKey,
      apiVersion: '2'
    });
  }

  getTools() {
    return Object.entries(toolSchemas).map(([name, schema]) => ({
      name,
      description: schema.description || `Execute ${name} operation in JIRA`,
      inputSchema: schema
    }));
  }

  async executeTool(name: string, args: any): Promise<Tool.Response> {
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
        throw new ToolError(error.message);
      }
      throw new ToolError('An unknown error occurred');
    }
  }

  private async jqlSearch(args: any): Promise<Tool.Response> {
    const { jql, nextPageToken, maxResults, fields, expand } = args;
    
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

  private async getIssue(args: any): Promise<Tool.Response> {
    const { issueIdOrKey, fields, expand, properties } = args;
    
    const issue = await this.jira.findIssue(issueIdOrKey, {
      fields: fields?.join(','),
      expand: expand,
      properties: properties?.join(',')
    });

    return {
      type: 'application/json',
      content: JSON.stringify(issue, null, 2)
    };
  }

  private async createIssue(args: any): Promise<Tool.Response> {
    const { project, summary, description, issueType, priority, assignee, labels, storyPoints, epic } = args;
    
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

  private async planSprint(args: any): Promise<Tool.Response> {
    const { projectKey, sprintName, sprintGoal, startDate, endDate, teamCapacity } = args;

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

    // Create sprint
    const boards = await this.jira.getAllBoards({ projectKeyOrId: projectKey });
    const scrum_board = boards.values.find(board => board.type === 'scrum');
    
    if (!scrum_board) {
      throw new Error('No Scrum board found for project');
    }

    const sprint = await this.jira.createSprint({
      name: sprintName,
      goal: sprintGoal,
      startDate,
      endDate,
      originBoardId: scrum_board.id
    });

    // Move issues to sprint
    await this.jira.moveIssuesToSprint(
      sprint.id,
      plannedIssues.map(issue => issue.id)
    );

    return {
      type: 'application/json',
      content: JSON.stringify({
        sprint,
        plannedIssues,
        totalStoryPoints: totalPoints,
        remainingCapacity: teamCapacity - totalPoints
      }, null, 2)
    };
  }
}
