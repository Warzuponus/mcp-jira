"""
JiraClient class implementation for MCP Jira.
Handles all direct interactions with the Jira API.
"""

from typing import List, Optional, Dict, Any
import aiohttp
import logging
from datetime import datetime
from base64 import b64encode

from .types import (
    Issue, Sprint, TeamMember, IssueType, 
    Priority, IssueStatus, SprintStatus,
    JiraError
)
from .config import Settings

logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, settings: Settings):
        self.base_url = str(settings.jira_url).rstrip('/')
        self.auth_header = self._create_auth_header(
            settings.jira_username,
            settings.jira_api_token
        )
        self.project_key = settings.project_key
        self.board_id = settings.default_board_id

    async def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: IssueType,
        priority: Priority,
        story_points: Optional[float] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None
    ) -> str:
        """Create a new Jira issue."""
        data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type.value},
                "priority": {"name": priority.value}
            }
        }

        if story_points:
            data["fields"]["customfield_10026"] = story_points  # Adjust field ID as needed
        if assignee:
            data["fields"]["assignee"] = {"name": assignee}
        if labels:
            data["fields"]["labels"] = labels
        if components:
            data["fields"]["components"] = [{"name": c} for c in components]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/rest/api/2/issue",
                headers=self._get_headers(),
                json=data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    return result["key"]
                else:
                    error_data = await response.text()
                    raise JiraError(f"Failed to create issue: {error_data}")

    async def get_sprint(self, sprint_id: int) -> Sprint:
        """Get sprint details by ID."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._convert_to_sprint(data)
                else:
                    error_data = await response.text()
                    raise JiraError(f"Failed to get sprint: {error_data}")

    async def get_active_sprint(self) -> Optional[Sprint]:
        """Get the currently active sprint."""
        sprints = await self._get_board_sprints(
            self.board_id, 
            state=SprintStatus.ACTIVE
        )
        return sprints[0] if sprints else None

    async def get_sprint_issues(self, sprint_id: int) -> List[Issue]:
        """Get all issues in a sprint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._convert_to_issue(i) for i in data["issues"]]
                else:
                    error_data = await response.text()
                    raise JiraError(f"Failed to get sprint issues: {error_data}")

    async def get_backlog_issues(self) -> List[Issue]:
        """Get all backlog issues."""
        jql = f"project = {self.project_key} AND sprint is EMPTY ORDER BY Rank ASC"
        return await self.search_issues(jql)

    async def get_assigned_issues(self, username: str) -> List[Issue]:
        """Get issues assigned to a specific user."""
        jql = f"assignee = {username} AND resolution = Unresolved"
        return await self.search_issues(jql)

    async def search_issues(self, jql: str) -> List[Issue]:
        """Search issues using JQL."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/rest/api/2/search",
                headers=self._get_headers(),
                json={
                    "jql": jql,
                    "maxResults": 100
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._convert_to_issue(i) for i in data["issues"]]
                else:
                    error_data = await response.text()
                    raise JiraError(f"Failed to search issues: {error_data}")

    async def get_issue_history(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get the change history of an issue."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/rest/api/2/issue/{issue_key}/changelog",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_changelog(data["values"])
                else:
                    error_data = await response.text()
                    raise JiraError(f"Failed to get issue history: {error_data}")

    # Helper methods
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Jira API requests."""
        return {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _create_auth_header(self, username: str, api_token: str) -> str:
        """Create base64 encoded auth header."""
        auth_string = f"{username}:{api_token}"
        return b64encode(auth_string.encode()).decode()

    def _convert_to_issue(self, data: Dict[str, Any]) -> Issue:
        """Convert Jira API response to Issue object."""
        fields = data["fields"]
        return Issue(
            key=data["key"],
            summary=fields["summary"],
            description=fields.get("description"),
            issue_type=IssueType(fields["issuetype"]["name"]),
            priority=Priority(fields["priority"]["name"]),
            status=IssueStatus(fields["status"]["name"]),
            assignee=self._convert_to_team_member(fields.get("assignee")) if fields.get("assignee") else None,
            story_points=fields.get("customfield_10026"),  # Adjust field ID as needed
            labels=fields.get("labels", []),
            components=[c["name"] for c in fields.get("components", [])],
            created_at=datetime.fromisoformat(fields["created"].rstrip('Z')),
            updated_at=datetime.fromisoformat(fields["updated"].rstrip('Z')),
            blocked_by=[],  # Would need to implement logic to determine blockers
            blocks=[]
        )

    def _convert_to_sprint(self, data: Dict[str, Any]) -> Sprint:
        """Convert Jira API response to Sprint object."""
        return Sprint(
            id=data["id"],
            name=data["name"],
            goal=data.get("goal"),
            status=SprintStatus(data["state"]),
            start_date=datetime.fromisoformat(data["startDate"].rstrip('Z')) if data.get("startDate") else None,
            end_date=datetime.fromisoformat(data["endDate"].rstrip('Z')) if data.get("endDate") else None
        )

    def _convert_to_team_member(self, data: Dict[str, Any]) -> TeamMember:
        """Convert Jira API response to TeamMember object."""
        return TeamMember(
            username=data["name"],
            display_name=data["displayName"],
            email=data.get("emailAddress")
        )

    def _process_changelog(self, changelog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process issue changelog into a more usable format."""
        history = []
        for entry in changelog:
            for item in entry["items"]:
                if item["field"] == "status":
                    history.append({
                        "from_status": item["fromString"],
                        "to_status": item["toString"],
                        "from_date": datetime.fromisoformat(entry["created"].rstrip('Z')),
                        "author": entry["author"]["displayName"]
                    })
        return history

    async def _get_board_sprints(
        self, 
        board_id: int, 
        state: Optional[SprintStatus] = None
    ) -> List[Sprint]:
        """Get all sprints for a board."""
        params = {"state": state.value} if state else {}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint",
                headers=self._get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._convert_to_sprint(s) for s in data["values"]]
                else:
                    error_data = await response.text()
                    raise JiraError(f"Failed to get board sprints: {error_data}")
