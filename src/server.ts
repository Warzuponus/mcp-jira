import {
  BaseServer,
  Tool,
  Resource,
  ResourceTemplate,
  ToolError,
} from '@modelcontextprotocol/sdk';
import JiraApi from 'jira-client';
import { JiraConfig, SprintPlanningInput } from './types';

export class JiraMCPServer extends BaseServer {
  private jira: JiraApi;
  private projectCache: Map<string, any> = new Map();

  constructor(config: JiraConfig) {
    super();
    this.jira = new JiraApi({
      protocol: config.protocol,
      host: config.host,
      username: config.username,
      password: config.password,
      apiVersion: config.apiVersion,
    });

    // Register project management tools
    this.registerTool('getProjectOverview', this.getProjectOverview.bind(this));
    this.registerTool('createSprint', this.createSprint.bind(this));
    this.registerTool('planSprint', this.planSprint.bind(this));
    this.registerTool('assignIssue', this.assignIssue.bind(this));
    this.registerTool('updatePriority', this.updatePriority.bind(this));
    this.registerTool('setDueDate', this.setDueDate.bind(this));
    this.registerTool('createEpic', this.createEpic.bind(this));
    this.registerTool('analyzeProjectMetrics', this.analyzeProjectMetrics.bind(this));
    
    // Register basic issue management tools
    this.registerTool('createIssue', this.createIssue.bind(this));
    this.registerTool('updateIssue', this.updateIssue.bind(this));
    this.registerTool('searchIssues', this.searchIssues.bind(this));
    
    // Register resource templates
    this.registerResourceTemplate('project', this.getProjectResource.bind(this));
    this.registerResourceTemplate('sprint', this.getSprintResource.bind(this));
    this.registerResourceTemplate('issue', this.getIssueResource.bind(this));
  }

  async start(): Promise<void> {
    // Initialize any necessary resources
    console.log('MCP JIRA Server started');
  }

  // Project Overview Tool
  private async getProjectOverview(params: any): Promise<Tool.Response> {
    try {
      const { projectKey } = params;
      
      const project = await this.jira.getProject(projectKey);
      
      const issues = await this.jira.searchJira(`project = ${projectKey}`, {
        maxResults: 1000,
        fields: ['summary', 'status', 'priority', 'assignee', 'duedate', 'customfield_10016']
      });

      const boards = await this.jira.getAllBoards(projectKey);
      const activeSprints = [];
      for (const board of boards.values) {
        const sprints = await this.jira.getAllSprints(board.id);
        activeSprints.push(...sprints.values.filter((sprint: any) => sprint.state === 'active'));
      }

      const metrics: any = {
        totalIssues: issues.total,
        issuesByStatus: {},
        issuesByPriority: {},
        averageStoryPoints: 0,
        backlogSize: 0
      };

      let totalStoryPoints = 0;
      let issuesWithPoints = 0;

      issues.issues.forEach((issue: any) => {
        metrics.issuesByStatus[issue.fields.status.name] = 
          (metrics.issuesByStatus[issue.fields.status.name] || 0) + 1;

        metrics.issuesByPriority[issue.fields.priority.name] = 
          (metrics.issuesByPriority[issue.fields.priority.name] || 0) + 1;

        if (issue.fields.customfield_10016) {
          totalStoryPoints += issue.fields.customfield_10016;
          issuesWithPoints++;
        }

        if (issue.fields.status.statusCategory.key === 'new') {
          metrics.backlogSize++;
        }
      });

      metrics.averageStoryPoints = issuesWithPoints ? totalStoryPoints / issuesWithPoints : 0;

      return {
        type: 'application/json',
        content: JSON.stringify({
          project,
          metrics,
          activeSprints
        })
      };
    } catch (error) {
      throw new ToolError('Failed to get project overview', { cause: error });
    }
  }

  // Add remaining methods here...
}

export function createServer(config: JiraConfig): JiraMCPServer {
  return new JiraMCPServer(config);
}