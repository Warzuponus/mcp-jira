import {
  MCPServer,
  Tool,
  Resource,
  ResourceTemplate,
  ToolError,
} from '@modelcontextprotocol/sdk';
import JiraApi from 'jira-client';

// JIRA client configuration
interface JiraConfig {
  protocol: string;
  host: string;
  username: string;
  password: string;
  apiVersion: string;
}

export class JiraMCPServer extends MCPServer {
  private jira: JiraApi;

  constructor(config: JiraConfig) {
    super();
    this.jira = new JiraApi({
      protocol: config.protocol,
      host: config.host,
      username: config.username,
      password: config.password,
      apiVersion: config.apiVersion,
    });

    // Register tools
    this.registerTool('createIssue', this.createIssue.bind(this));
    this.registerTool('updateIssue', this.updateIssue.bind(this));
    this.registerTool('searchIssues', this.searchIssues.bind(this));
    
    // Register resource templates
    this.registerResourceTemplate('issue', this.getIssueResource.bind(this));
  }

  // Tool: Create JIRA Issue
  private async createIssue(params: any): Promise<Tool.Response> {
    try {
      const { project, summary, description, issueType } = params;
      
      const issue = await this.jira.addNewIssue({
        fields: {
          project: { key: project },
          summary,
          description,
          issuetype: { name: issueType },
        },
      });

      return {
        type: 'text/plain',
        content: `Created issue ${issue.key}: ${issue.self}`,
      };
    } catch (error) {
      throw new ToolError('Failed to create issue', { cause: error });
    }
  }

  // Tool: Update JIRA Issue
  private async updateIssue(params: any): Promise<Tool.Response> {
    try {
      const { issueKey, summary, description, status } = params;
      
      await this.jira.updateIssue(issueKey, {
        fields: {
          summary,
          description,
          status: status ? { name: status } : undefined,
        },
      });

      return {
        type: 'text/plain',
        content: `Updated issue ${issueKey}`,
      };
    } catch (error) {
      throw new ToolError('Failed to update issue', { cause: error });
    }
  }

  // Tool: Search JIRA Issues
  private async searchIssues(params: any): Promise<Tool.Response> {
    try {
      const { jql, maxResults = 10 } = params;
      
      const results = await this.jira.searchJira(jql, {
        maxResults,
      });

      return {
        type: 'application/json',
        content: JSON.stringify(results.issues),
      };
    } catch (error) {
      throw new ToolError('Failed to search issues', { cause: error });
    }
  }

  // Resource Template: Get Issue Details
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
        content: JSON.stringify(issue),
      };
    } catch (error) {
      throw new Error(`Failed to get issue: ${error.message}`);
    }
  }
}

// Export server creation function
export function createServer(config: JiraConfig): JiraMCPServer {
  return new JiraMCPServer(config);
}