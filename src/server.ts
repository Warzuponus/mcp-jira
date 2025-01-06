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
  // Add methods...
}

export function createServer(config: JiraConfig): JiraMCPServer {
  return new JiraMCPServer(config);
}