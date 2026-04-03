"""
JiraClient class implementation for MCP Jira.
Handles all direct interactions with the Jira API.
"""

from typing import List, Optional, Dict, Any
import aiohttp
import logging
from datetime import datetime, timezone
from base64 import b64encode

from .types import (
    Issue, Sprint, TeamMember, IssueType,
    Priority, IssueStatus, SprintStatus,
    JiraError
)
from .config import Settings

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


class JiraClient:
    def __init__(self, settings: Settings):
        self.base_url = str(settings.jira_url).rstrip('/')
        self.auth_header = self._create_auth_header(
            settings.jira_username,
            settings.jira_api_token.get_secret_value()
        )
        self.project_key = settings.project_key
        self.board_id = settings.default_board_id
        self.story_points_field = settings.story_points_field
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=settings.jira_request_timeout)

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self._get_headers()
            )
        return self.session

    async def close(self):
        """Close the API client session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    # ------------------------------------------------------------------ #
    #  Retry helper
    # ------------------------------------------------------------------ #

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> aiohttp.ClientResponse:
        """
        Execute an HTTP request with exponential backoff on transient errors.
        Returns the response object (caller must check status).
        """
        import asyncio

        session = await self.get_session()
        last_error: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await session.request(method, url, **kwargs)

                # Retry on 429 (rate limited) or 503 (service unavailable)
                if response.status in (429, 503) and attempt < MAX_RETRIES - 1:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Jira returned %d, retrying in %.1fs (attempt %d/%d)",
                        response.status, delay, attempt + 1, MAX_RETRIES,
                    )
                    response.release()
                    await asyncio.sleep(delay)
                    continue

                return response

            except (aiohttp.ClientError, TimeoutError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Request to %s failed (%s), retrying in %.1fs (attempt %d/%d)",
                        url, exc, delay, attempt + 1, MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)

        raise JiraError(f"Request to {url} failed after {MAX_RETRIES} attempts: {last_error}")

    # ------------------------------------------------------------------ #
    #  Public API methods
    # ------------------------------------------------------------------ #

    async def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: IssueType,
        priority: Priority,
        story_points: Optional[float] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        project_key: Optional[str] = None
    ) -> str:
        """Create a new Jira issue."""
        # Convert plain text description to Atlassian Document Format (ADF)
        adf_description = self._text_to_adf(description)

        # Use provided project key or fall back to default
        target_project = project_key or self.project_key

        data: Dict[str, Any] = {
            "fields": {
                "project": {"key": target_project},
                "summary": summary,
                "description": adf_description,
                "issuetype": {"name": issue_type.value},
                "priority": {"name": priority.value}
            }
        }

        if story_points:
            data["fields"][self.story_points_field] = story_points
        if assignee:
            data["fields"]["assignee"] = {"accountId": assignee}  # API v3 uses accountId
        if labels:
            data["fields"]["labels"] = labels
        if components:
            data["fields"]["components"] = [{"name": c} for c in components]

        response = await self._request_with_retry(
            "POST",
            f"{self.base_url}/rest/api/3/issue",
            json=data,
        )
        if response.status == 201:
            result = await response.json()
            return result["key"]
        else:
            error_data = await response.text()
            raise JiraError(f"Failed to create issue: {error_data}")

    async def get_sprint(self, sprint_id: int) -> Sprint:
        """Get sprint details by ID."""
        response = await self._request_with_retry(
            "GET",
            f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}",
        )
        if response.status == 200:
            data = await response.json()
            return self._convert_to_sprint(data)
        else:
            error_data = await response.text()
            raise JiraError(f"Failed to get sprint: {error_data}")

    async def get_active_sprint(self, board_id: Optional[int] = None) -> Optional[Sprint]:
        """Get the currently active sprint."""
        target_board = board_id or self.board_id
        if not target_board:
            # If no board provided and no default, we can't find sprint
            return None

        sprints = await self._get_board_sprints(
            target_board,
            state=SprintStatus.ACTIVE
        )
        return sprints[0] if sprints else None

    async def get_sprint_issues(self, sprint_id: int, max_results: int = 200) -> List[Issue]:
        """Get all issues in a sprint with pagination."""
        all_issues: List[Issue] = []
        start_at = 0

        while True:
            response = await self._request_with_retry(
                "GET",
                f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue",
                params={"startAt": start_at, "maxResults": min(max_results - len(all_issues), 50)},
            )
            if response.status == 200:
                data = await response.json()
                issues = [self._convert_to_issue(i) for i in data["issues"]]
                all_issues.extend(issues)

                # Check if there are more pages
                if len(all_issues) >= data.get("total", 0) or len(all_issues) >= max_results:
                    break
                start_at = len(all_issues)
            else:
                error_data = await response.text()
                raise JiraError(f"Failed to get sprint issues: {error_data}")

        return all_issues

    async def get_backlog_issues(self, project_key: Optional[str] = None) -> List[Issue]:
        """Get all backlog issues."""
        target_project = project_key or self.project_key
        jql = f"project = {target_project} AND sprint is EMPTY ORDER BY Rank ASC"
        return await self.search_issues(jql)

    async def get_assigned_issues(self, username: str) -> List[Issue]:
        """Get issues assigned to a specific user."""
        jql = f"assignee = {username} AND resolution = Unresolved"
        return await self.search_issues(jql)

    async def search_issues(self, jql: str, max_results: int = 100) -> List[Issue]:
        """Search issues using JQL with cursor-based pagination (search/jql API)."""
        all_issues: List[Issue] = []
        next_page_token: Optional[str] = None

        while True:
            body: Dict[str, Any] = {
                "jql": jql,
                "maxResults": min(max_results - len(all_issues), 50),
                "fields": [
                    "summary", "description", "issuetype", "priority",
                    "status", "assignee", "labels", "components",
                    "created", "updated", self.story_points_field
                ]
            }
            if next_page_token:
                body["nextPageToken"] = next_page_token

            response = await self._request_with_retry(
                "POST",
                f"{self.base_url}/rest/api/3/search/jql",
                json=body,
            )
            if response.status == 200:
                data = await response.json()
                issues = [self._convert_to_issue(i) for i in data["issues"]]
                all_issues.extend(issues)

                # Cursor-based pagination: stop when nextPageToken is absent or limit reached
                next_page_token = data.get("nextPageToken")
                if not next_page_token or len(all_issues) >= max_results:
                    break
            else:
                error_data = await response.text()
                raise JiraError(f"Failed to search issues: {error_data}")

        return all_issues

    async def get_issue_history(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get the change history of an issue."""
        response = await self._request_with_retry(
            "GET",
            f"{self.base_url}/rest/api/3/issue/{issue_key}/changelog",
        )
        if response.status == 200:
            data = await response.json()
            return self._process_changelog(data["values"])
        else:
            error_data = await response.text()
            raise JiraError(f"Failed to get issue history: {error_data}")

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

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

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a Jira datetime string into a timezone-aware datetime."""
        if not date_str:
            return None
        # Jira returns ISO 8601 with timezone info or trailing Z
        cleaned = date_str.rstrip('Z')
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

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

        # Handle status — use flexible from_name to support custom statuses
        status_data = fields.get("status", {})
        status_name = status_data.get("name", "To Do") if status_data else "To Do"
        status = IssueStatus.from_name(status_name)

        # Handle dates — timezone-aware
        created_at = self._parse_datetime(fields.get("created")) or datetime.now(timezone.utc)
        updated_at = self._parse_datetime(fields.get("updated")) or datetime.now(timezone.utc)

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
            status_name=status_name,
            assignee=self._convert_to_team_member(fields.get("assignee")) if fields.get("assignee") else None,
            story_points=fields.get(self.story_points_field),
            labels=fields.get("labels", []),
            components=[c["name"] for c in fields.get("components", [])],
            created_at=created_at,
            updated_at=updated_at,
            blocked_by=[],
            blocks=[]
        )

    def _convert_to_sprint(self, data: Dict[str, Any]) -> Sprint:
        """Convert Jira API response to Sprint object."""
        # Normalize the state value for our enum (Jira uses lowercase)
        raw_state = data.get("state", "future")
        try:
            status = SprintStatus(raw_state.lower())
        except ValueError:
            logger.warning("Unknown sprint state '%s', defaulting to 'future'", raw_state)
            status = SprintStatus.FUTURE

        return Sprint(
            id=data["id"],
            name=data["name"],
            goal=data.get("goal"),
            status=status,
            start_date=self._parse_datetime(data.get("startDate")),
            end_date=self._parse_datetime(data.get("endDate")),
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
            for item in entry.get("items", []):
                if item["field"] == "status":
                    history.append({
                        "from_status": item["fromString"],
                        "to_status": item["toString"],
                        "from_date": self._parse_datetime(entry["created"]),
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
        response = await self._request_with_retry(
            "GET",
            f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint",
            params=params,
        )
        if response.status == 200:
            data = await response.json()
            return [self._convert_to_sprint(s) for s in data["values"]]
        else:
            error_data = await response.text()
            raise JiraError(f"Failed to get board sprints: {error_data}")
