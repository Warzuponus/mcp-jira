import {
  MCPServer,
  Tool,
  Resource,
  ResourceTemplate,
  ToolError,
} from '@modelcontextprotocol/sdk';
import JiraApi from 'jira-client';
import { JiraConfig, SprintPlanningInput } from './types';

export class JiraMCPServer extends MCPServer {
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

  // Project Overview Tool
  private async getProjectOverview(params: any): Promise<Tool.Response> {
    try {
      const { projectKey } = params;
      
      const project = await this.jira.getProject(projectKey);
      
      const issues = await this.jira.searchJira(`project = ${projectKey}`, {
        maxResults: 1000,
        fields: ['summary', 'status', 'priority', 'assignee', 'duedate', 'customfield_10016']
      });

      const boards = await this.jira.getAllBoards({ projectKeyOrId: projectKey });
      const activeSprints = [];
      for (const board of boards.values) {
        const sprints = await this.jira.getAllSprints(board.id);
        activeSprints.push(...sprints.values.filter(sprint => sprint.state === 'active'));
      }

      const metrics = {
        totalIssues: issues.total,
        issuesByStatus: {},
        issuesByPriority: {},
        averageStoryPoints: 0,
        backlogSize: 0
      };

      let totalStoryPoints = 0;
      let issuesWithPoints = 0;

      issues.issues.forEach(issue => {
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

  // Sprint Planning Tool
  private async planSprint(params: SprintPlanningInput): Promise<Tool.Response> {
    try {
      const { projectKey, sprintName, sprintGoal, startDate, endDate, teamCapacity } = params;

      const backlogIssues = await this.jira.searchJira(
        `project = ${projectKey} AND status = Backlog ORDER BY priority DESC, created ASC`,
        { maxResults: 100 }
      );

      const plannedIssues = [];
      let totalPoints = 0;

      for (const issue of backlogIssues.issues) {
        const storyPoints = issue.fields.customfield_10016 || 0;
        if (totalPoints + storyPoints <= teamCapacity) {
          plannedIssues.push(issue);
          totalPoints += storyPoints;
        }
      }

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
        })
      };
    } catch (error) {
      throw new ToolError('Failed to plan sprint', { cause: error });
    }
  }

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
      throw new Error(`Failed to get project: ${error.message}`);
    }
  }

  private async getSprintResource(params: ResourceTemplate.Parameters): Promise<Resource> {
    const sprintId = params.get('sprintId');
    if (!sprintId) {
      throw new Error('Sprint ID is required');
    }

    try {
      const sprint = await this.jira.getSprint(sprintId);
      
      return {
        uri: `jira://sprint/${sprintId}`,
        type: 'application/json',
        content: JSON.stringify(sprint)
      };
    } catch (error) {
      throw new Error(`Failed to get sprint: ${error.message}`);
    }
  }

  private async getIssueResource(params: ResourceTemplate.Parameters): Promise<Resource> {
    const issueKey = params.get('issueKey');
    if (!issueKey) {
      throw new Error('Issue key is required');
    }

    try {
      const issue = await this.jira.findIssue(issueKey);
      
      return {
        uri: `jira://issue/${issueKey}`,
        type: 'application/json',
        content: JSON.stringify(issue)
      };
    } catch (error) {
      throw new Error(`Failed to get issue: ${error.message}`);
    }
  }
}

export function createServer(config: JiraConfig): JiraMCPServer {
  return new JiraMCPServer(config);
}