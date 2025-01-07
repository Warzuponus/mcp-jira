import { BaseServer, Tool, Resource, ResourceTemplate, ToolError } from '@modelcontextprotocol/sdk';
import JiraApi from 'jira-client';
import { JiraConfig, SprintPlanningInput } from './types';

export class JiraMCPServer extends BaseServer {
  protected readonly tools: Map<string, Tool> = new Map();
  protected readonly resourceTemplates: Map<string, ResourceTemplate> = new Map();
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

    this.initializeTools();
    this.initializeResources();
  }

  private initializeTools(): void {
    // Register project management tools
    this.tools.set('getProjectOverview', this.getProjectOverview.bind(this));
    this.tools.set('createSprint', this.createSprint.bind(this));
    this.tools.set('planSprint', this.planSprint.bind(this));
    this.tools.set('assignIssue', this.assignIssue.bind(this));
    this.tools.set('updatePriority', this.updatePriority.bind(this));
    this.tools.set('setDueDate', this.setDueDate.bind(this));
    this.tools.set('createEpic', this.createEpic.bind(this));
    this.tools.set('analyzeProjectMetrics', this.analyzeProjectMetrics.bind(this));
    
    // Register basic issue management tools
    this.tools.set('createIssue', this.createIssue.bind(this));
    this.tools.set('updateIssue', this.updateIssue.bind(this));
    this.tools.set('searchIssues', this.searchIssues.bind(this));
  }

  private initializeResources(): void {
    // Register resource templates
    this.resourceTemplates.set('project', this.getProjectResource.bind(this));
    this.resourceTemplates.set('sprint', this.getSprintResource.bind(this));
    this.resourceTemplates.set('issue', this.getIssueResource.bind(this));
  }

  async start(): Promise<void> {
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

      // Using the correct method signature for getAllBoards
      const boards = await this.jira.getAllBoards(projectKey as number);
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
      if (error instanceof Error) {
        throw new ToolError('Failed to get project overview: ' + error.message);
      }
      throw new ToolError('Failed to get project overview');
    }
  }

  // Declare other tool methods
  private async createSprint(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async planSprint(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async assignIssue(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async updatePriority(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async setDueDate(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async createEpic(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async analyzeProjectMetrics(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async createIssue(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async updateIssue(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }
  private async searchIssues(params: any): Promise<Tool.Response> { throw new Error('Not implemented'); }

  // Resource handlers
  private async getProjectResource(params: ResourceTemplate.Parameters): Promise<Resource> {
    const projectKey = params.get('projectKey');
    if (!projectKey) {
      throw new Error('Project key is required');
    }

    try {
      if (!this.projectCache.has(projectKey)) {
        const project = await this.jira.getProject(projectKey);
        this.projectCache.set(projectKey, project);
      }

      return {
        uri: `jira://project/${projectKey}`,
        type: 'application/json',
        content: JSON.stringify(this.projectCache.get(projectKey))
      };
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to get project: ${error.message}`);
      }
      throw new Error('Failed to get project');
    }
  }

  private async getSprintResource(params: ResourceTemplate.Parameters): Promise<Resource> {
    throw new Error('Not implemented');
  }

  private async getIssueResource(params: ResourceTemplate.Parameters): Promise<Resource> {
    throw new Error('Not implemented');
  }
}

export function createServer(config: JiraConfig): JiraMCPServer {
  return new JiraMCPServer(config);
}