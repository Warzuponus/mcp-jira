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

  // Create Sprint Tool
  private async createSprint(params: any): Promise<Tool.Response> {
    try {
      const { projectKey, name, goal, startDate, endDate } = params;
      
      // Get Scrum board for project
      const boards = await this.jira.getAllBoards({ projectKeyOrId: projectKey });
      const scrum_board = boards.values.find(board => board.type === 'scrum');
      
      if (!scrum_board) {
        throw new Error('No Scrum board found for project');
      }

      const sprint = await this.jira.createSprint({
        name,
        goal,
        startDate,
        endDate,
        originBoardId: scrum_board.id
      });

      return {
        type: 'application/json',
        content: JSON.stringify(sprint)
      };
    } catch (error) {
      throw new ToolError('Failed to create sprint', { cause: error });
    }
  }

  // Enhanced searchIssues tool with additional functionality
  private async searchIssues(params: any): Promise<Tool.Response> {
    try {
      const { jql, maxResults = 50, fields = [] } = params;
      
      // Default fields to return if none specified
      const defaultFields = [
        'summary',
        'status',
        'priority',
        'assignee',
        'duedate',
        'issuetype',
        'customfield_10016', // Story points
        'labels',
        'components',
        'created',
        'updated'
      ];

      const results = await this.jira.searchJira(jql, {
        maxResults,
        fields: fields.length > 0 ? fields : defaultFields
      });

      return {
        type: 'application/json',
        content: JSON.stringify(results.issues)
      };
    } catch (error) {
      throw new ToolError('Failed to search issues', { cause: error });
    }
  }

  // Enhanced updateIssue tool with additional functionality
  private async updateIssue(params: any): Promise<Tool.Response> {
    try {
      const { 
        issueKey,
        summary,
        description,
        status,
        priority,
        assignee,
        labels,
        storyPoints,
        components,
        epic,
        dueDate,
        estimate
      } = params;
      
      const updateData: any = {
        fields: {}
      };

      // Only include fields that are provided
      if (summary) updateData.fields.summary = summary;
      if (description) updateData.fields.description = description;
      if (status) updateData.fields.status = { name: status };
      if (priority) updateData.fields.priority = { name: priority };
      if (assignee) updateData.fields.assignee = { name: assignee };
      if (labels) updateData.fields.labels = labels;
      if (storyPoints) updateData.fields.customfield_10016 = storyPoints;
      if (components) updateData.fields.components = components.map(name => ({ name }));
      if (epic) updateData.fields.customfield_10014 = epic;
      if (dueDate) updateData.fields.duedate = dueDate;
      if (estimate) updateData.fields.timeoriginalestimate = estimate;

      await this.jira.updateIssue(issueKey, updateData);

      return {
        type: 'text/plain',
        content: `Updated issue ${issueKey}`
      };
    } catch (error) {
      throw new ToolError('Failed to update issue', { cause: error });
    }
  }
}

// Export server creation function
export function createServer(config: JiraConfig): JiraMCPServer {
  return new JiraMCPServer(config);
}
