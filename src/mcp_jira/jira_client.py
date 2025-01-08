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
            fields['customfield_10026'] = story_points  # Adjust field ID as needed

        issue = self.client.create_issue(fields=fields)
        
        if sprint_id:
            self.client.add_issues_to_sprint(sprint_id, [issue.key])

        return self._convert_to_issue(issue)

    async def get_sprint_metrics(self, sprint_id: int) -> SprintMetrics:
        """Get detailed metrics for a sprint"""
        sprint = self.client.sprint(sprint_id)
        issues = self.client.search_issues(
            f'sprint = {sprint_id} AND project = {self.project_key}')

        total_points = 0
        completed_points = 0
        sprint_issues = []

        for issue in issues:
            story_points = getattr(issue.fields, 'customfield_10026', 0) or 0
            total_points += story_points
            
            if issue.fields.status.name.lower() in ['done', 'completed']:
                completed_points += story_points

            sprint_issues.append(self._convert_to_issue(issue))

        return SprintMetrics(
            total_points=total_points,
            completed_points=completed_points,
            remaining_points=total_points - completed_points,
            completion_percentage=(completed_points / total_points * 100) if total_points > 0 else 0,
            issues=sprint_issues
        )

    async def update_issue(self, issue_key: str, 
                          fields: Dict[str, Any]) -> Issue:
        """Update an existing issue"""
        issue = self.client.issue(issue_key)
        issue.update(fields=fields)
        return self._convert_to_issue(issue)

    async def get_active_sprint(self) -> Optional[Sprint]:
        """Get the currently active sprint"""
        board_id = settings.DEFAULT_BOARD_ID
        sprints = self.client.sprints(board_id, state='active')
        if sprints:
            sprint = sprints[0]
            return Sprint(
                id=sprint.id,
                name=sprint.name,
                status=sprint.state,
                start_date=sprint.startDate,
                end_date=sprint.endDate,
                goal=getattr(sprint, 'goal', None)
            )
        return None

    async def get_issue(self, issue_key: str) -> Issue:
        """Get a specific issue by key"""
        issue = self.client.issue(issue_key)
        return self._convert_to_issue(issue)

    async def search_issues(self, jql: str, max_results: int = 50) -> List[Issue]:
        """Search for issues using JQL"""
        issues = self.client.search_issues(jql, maxResults=max_results)
        return [self._convert_to_issue(issue) for issue in issues]

    def _convert_to_issue(self, jira_issue) -> Issue:
        """Convert a JIRA issue to our Issue model"""
        fields = jira_issue.fields
        return Issue(
            key=jira_issue.key,
            summary=fields.summary,
            description=fields.description,
            issue_type=IssueType(fields.issuetype.name),
            priority=Priority(fields.priority.name) if fields.priority else None,
            assignee=fields.assignee.name if fields.assignee else None,
            story_points=getattr(fields, 'customfield_10026', None),
            sprint=fields.sprint.name if hasattr(fields, 'sprint') and fields.sprint else None,
            status=fields.status.name
        )