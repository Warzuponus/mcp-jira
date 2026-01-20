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
            settings.jira_api_token.get_secret_value()
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
        # Convert plain text description to Atlassian Document Format (ADF)
        adf_description = self._text_to_adf(description)

        data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": adf_description,
                "issuetype": {"name": issue_type.value},
                "priority": {"name": priority.value}
            }
        }

        if story_points:
            data["fields"]["customfield_10026"] = story_points  # Adjust field ID as needed
        if assignee:
            data["fields"]["assignee"] = {"accountId": assignee}  # API v3 uses accountId
        if labels:
            data["fields"]["labels"] = labels
        if components:
            data["fields"]["components"] = [{"name": c} for c in components]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/rest/api/3/issue",
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

    async def search_issues(self, jql: str, max_results: int = 100) -> List[Issue]:
        """Search issues using JQL (API v3)."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/rest/api/3/search/jql",
                headers=self._get_headers(),
                json={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": [
                        "summary", "description", "issuetype", "priority",
                        "status", "assignee", "labels", "components",
                        "created", "updated", "customfield_10026"
                    ]
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
                f"{self.base_url}/rest/api/3/issue/{issue_key}/changelog",
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

    def _text_to_adf(self, text: str) -> Dict[str, Any]:
        """Convert plain text/markdown to Atlassian Document Format (ADF)."""
        if not text:
            return {
                "type": "doc",
                "version": 1,
                "content": []
            }

        content = []
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Handle headers
            if line.startswith('### '):
                content.append({
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": line[4:]}]
                })
            elif line.startswith('## '):
                content.append({
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": line[3:]}]
                })
            elif line.startswith('# '):
                content.append({
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": line[2:]}]
                })
            # Handle bullet points
            elif line.startswith('- ') or line.startswith('* '):
                # Collect all consecutive bullet points
                bullet_items = []
                while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                    bullet_text = lines[i][2:]
                    bullet_items.append({
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": bullet_text}]
                        }]
                    })
                    i += 1
                content.append({
                    "type": "bulletList",
                    "content": bullet_items
                })
                continue  # Skip the i += 1 at the end
            # Handle empty lines (skip)
            elif line.strip() == '':
                pass
            # Regular paragraph
            else:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": line}]
                })

            i += 1

        return {
            "type": "doc",
            "version": 1,
            "content": content
        }

    def _adf_to_text(self, adf: Dict[str, Any]) -> str:
        """Convert Atlassian Document Format (ADF) to plain text."""
        if not adf or not isinstance(adf, dict):
            return ""

        def extract_text(node: Dict[str, Any]) -> str:
            """Recursively extract text from ADF nodes."""
            if not isinstance(node, dict):
                return ""

            text_parts = []
            node_type = node.get("type", "")

            # Handle text nodes
            if node_type == "text":
                return node.get("text", "")

            # Handle heading nodes
            if node_type == "heading":
                level = node.get("attrs", {}).get("level", 1)
                prefix = "#" * level + " "
                content_text = "".join(extract_text(c) for c in node.get("content", []))
                return prefix + content_text + "\n"

            # Handle paragraph nodes
            if node_type == "paragraph":
                content_text = "".join(extract_text(c) for c in node.get("content", []))
                return content_text + "\n"

            # Handle list items
            if node_type == "listItem":
                content_text = "".join(extract_text(c) for c in node.get("content", []))
                return "- " + content_text.strip() + "\n"

            # Handle bullet lists
            if node_type == "bulletList":
                return "".join(extract_text(c) for c in node.get("content", []))

            # Handle other nodes with content
            if "content" in node:
                return "".join(extract_text(c) for c in node.get("content", []))

            return ""

        return extract_text(adf).strip()

    def _create_auth_header(self, username: str, api_token: str) -> str:
        """Create base64 encoded auth header."""
        auth_string = f"{username}:{api_token}"
        return b64encode(auth_string.encode()).decode()

    def _convert_to_issue(self, data: Dict[str, Any]) -> Issue:
        """Convert Jira API response to Issue object."""
        fields = data.get("fields", {})

        # Handle issue type - try to get name, fallback to "Task"
        issue_type_data = fields.get("issuetype", {})
        issue_type_name = issue_type_data.get("name", "Task") if issue_type_data else "Task"
        try:
            issue_type = IssueType(issue_type_name)
        except ValueError:
            issue_type = IssueType.TASK

        # Handle priority - try to get name, fallback to "Medium"
        priority_data = fields.get("priority", {})
        priority_name = priority_data.get("name", "Medium") if priority_data else "Medium"
        try:
            priority = Priority(priority_name)
        except ValueError:
            priority = Priority.MEDIUM

        # Handle status - try to get name, fallback to "To Do"
        status_data = fields.get("status", {})
        status_name = status_data.get("name", "To Do") if status_data else "To Do"
        try:
            status = IssueStatus(status_name)
        except ValueError:
            status = IssueStatus.TODO

        # Handle dates
        created_str = fields.get("created")
        updated_str = fields.get("updated")
        created_at = datetime.fromisoformat(created_str.rstrip('Z')) if created_str else datetime.now()
        updated_at = datetime.fromisoformat(updated_str.rstrip('Z')) if updated_str else datetime.now()

        # Convert ADF description to plain text
        description = fields.get("description")
        if isinstance(description, dict):
            description = self._adf_to_text(description)

        return Issue(
            key=data.get("key", "UNKNOWN"),
            summary=fields.get("summary", ""),
            description=description,
            issue_type=issue_type,
            priority=priority,
            status=status,
            assignee=self._convert_to_team_member(fields.get("assignee")) if fields.get("assignee") else None,
            story_points=fields.get("customfield_10026"),
            labels=fields.get("labels", []),
            components=[c["name"] for c in fields.get("components", [])],
            created_at=created_at,
            updated_at=updated_at,
            blocked_by=[],
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
            username=data.get("accountId", data.get("name", "")),
            display_name=data.get("displayName", ""),
            email=data.get("emailAddress"),
            role=None
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
