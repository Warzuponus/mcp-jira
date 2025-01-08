from jira import JIRA
from typing import List, Optional, Dict, Any
from .config import settings
from .types import Issue, Sprint, SprintMetrics, Priority, IssueType

class JiraClient:
    def __init__(self):
        self.client = JIRA(
            server=settings.JIRA_URL,
            basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)
        )
        self.project_key = settings.PROJECT_KEY

    async def create_issue(self, summary: str, description: str,
                          issue_type: IssueType,
                          priority: Optional[Priority] = None,
                          assignee: Optional[str] = None,
                          story_points: Optional[float] = None,
                          sprint_id: Optional[int] = None) -> Issue:
        """Create a new Jira issue"""
        fields = {
            'project': {'key': self.project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type.value}
        }

        if priority:
            fields['priority'] = {'name': priority.value}
        if assignee:
            fields['assignee'] = {'name': assignee}
        if story_points:
            fields['customfield_10026'] = story_points

        issue = self.client.create_issue(fields=fields)
        
        if sprint_id:
            self.client.add_issues_to_sprint(sprint_id, [issue.key])

        return self._convert_to_issue(issue)
