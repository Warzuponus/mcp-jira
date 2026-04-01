"""
Simple MCP server for Jira integration.
Implements core project management functions following MCP specification.
"""

import asyncio
import logging
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent, ImageContent, EmbeddedResource
)

from .jira_client import JiraClient
from .config import get_settings
from .types import IssueType, Priority

logger = logging.getLogger(__name__)

# Initialize server
server = Server("mcp-jira")

# Global client (will be initialized in main)
jira_client: Optional[JiraClient] = None


def _get_client() -> JiraClient:
    """Get the initialised Jira client or raise a clear error."""
    if jira_client is None:
        raise RuntimeError("Jira client not initialized")
    return jira_client


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools for Jira operations."""
    return [
        Tool(
            name="create_issue",
            description=(
                "Create a new Jira issue with a summary, detailed description, "
                "type (Story, Bug, Task, or Epic), and priority level "
                "(Highest, High, Medium, Low, Lowest). "
                "Optionally set story points, assign to a user by account ID, "
                "and target a specific project by its key."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Brief one-line summary of the issue"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue (supports basic markdown: headings, bullet lists)"
                    },
                    "issue_type": {
                        "type": "string",
                        "enum": ["Story", "Bug", "Task", "Epic"],
                        "description": "Type of issue to create"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["Highest", "High", "Medium", "Low", "Lowest"],
                        "description": "Priority level"
                    },
                    "story_points": {
                        "type": "number",
                        "description": "Story points estimate (optional)"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Jira account ID of the user to assign the issue to (optional)"
                    },
                    "project_key": {
                        "type": "string",
                        "description": "Project key to create issue in (optional, defaults to the configured default project)"
                    }
                },
                "required": ["summary", "description", "issue_type", "priority"]
            }
        ),
        Tool(
            name="search_issues",
            description=(
                "Search for Jira issues using JQL (Jira Query Language). "
                "Returns a formatted list of matching issues with status, priority, "
                "assignee, and story points. Supports any valid JQL expression."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string (e.g. 'project = PROJ AND status = \"In Progress\"')"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 20, max: 100)"
                    }
                },
                "required": ["jql"]
            }
        ),
        Tool(
            name="get_sprint_status",
            description=(
                "Get a comprehensive status report for a sprint including "
                "completion percentage, story points progress, days remaining, "
                "in-progress count, and blocked issue count. "
                "Uses the active sprint by default, or specify a sprint/board ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_id": {
                        "type": "number",
                        "description": "Sprint ID to analyze (optional, defaults to active sprint)"
                    },
                    "board_id": {
                        "type": "number",
                        "description": "Board ID to find active sprint in (optional, defaults to configured board)"
                    }
                }
            }
        ),
        Tool(
            name="get_team_workload",
            description=(
                "Analyze team workload and capacity for a list of team members. "
                "Shows each member's total assigned story points, number of "
                "active issues, and a workload indicator (green/yellow/red). "
                "Members are identified by their Jira username or account ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "team_members": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of team member usernames or account IDs to analyze"
                    }
                },
                "required": ["team_members"]
            }
        ),
        Tool(
            name="generate_standup_report",
            description=(
                "Generate a daily standup report for the active sprint. "
                "Includes sections for items completed yesterday, currently "
                "in-progress items, blocked items, and overall sprint metrics "
                "(points completed vs total, active/blocked counts)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "number",
                        "description": "Board ID to generate report for (optional, defaults to configured board)"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for Jira operations."""
    if not jira_client:
        return [TextContent(type="text", text="Error: Jira client not initialized")]

    try:
        if name == "create_issue":
            return await handle_create_issue(arguments)
        elif name == "search_issues":
            return await handle_search_issues(arguments)
        elif name == "get_sprint_status":
            return await handle_sprint_status(arguments)
        elif name == "get_team_workload":
            return await handle_team_workload(arguments)
        elif name == "generate_standup_report":
            return await handle_standup_report(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.exception(f"Error executing tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# Tool handlers
async def handle_create_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Handle create_issue tool call."""
    client = _get_client()
    issue_key = await client.create_issue(
        summary=args["summary"],
        description=args["description"],
        issue_type=IssueType(args["issue_type"]),
        priority=Priority(args["priority"]),
        story_points=args.get("story_points"),
        assignee=args.get("assignee"),
        project_key=args.get("project_key")
    )

    return [TextContent(
        type="text",
        text=f"✅ Created issue {issue_key}: {args['summary']}"
    )]

async def handle_search_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Handle search_issues tool call."""
    client = _get_client()
    jql = args["jql"]
    max_results = args.get("max_results", 20)

    issues = await client.search_issues(jql, max_results=max_results)

    if not issues:
        return [TextContent(type="text", text="No issues found matching the query.")]

    # Format results
    result_text = f"Found {len(issues)} issues:\n\n"
    for issue in issues:
        status_name = issue.status_name or issue.status.value
        status_emoji = "✅" if issue.status.value == "Done" else "🔄" if issue.status.value == "In Progress" else "📋"
        priority_emoji = "🔴" if issue.priority.value in ["Highest", "High"] else "🟡" if issue.priority.value == "Medium" else "🟢"

        assignee_text = f" (👤 {issue.assignee.display_name})" if issue.assignee else " (Unassigned)"
        points_text = f" [{issue.story_points}pts]" if issue.story_points else ""

        result_text += f"{status_emoji} **{issue.key}**: {issue.summary}\n"
        result_text += f"   {priority_emoji} {issue.priority.value} | {status_name}{assignee_text}{points_text}\n\n"

    return [TextContent(type="text", text=result_text)]

async def handle_sprint_status(args: Dict[str, Any]) -> List[TextContent]:
    """Handle get_sprint_status tool call."""
    client = _get_client()
    sprint_id = args.get("sprint_id")

    if sprint_id:
        sprint = await client.get_sprint(sprint_id)
    else:
        # Pass board_id if provided
        sprint = await client.get_active_sprint(board_id=args.get("board_id"))
        if not sprint:
            return [TextContent(type="text", text="No active sprint found.")]

    issues = await client.get_sprint_issues(sprint.id)

    # Calculate metrics
    total_points = sum(issue.story_points for issue in issues if issue.story_points)
    completed_points = sum(issue.story_points for issue in issues
                          if issue.story_points and issue.status.value == "Done")
    in_progress_count = len([i for i in issues if i.status.value == "In Progress"])
    blocked_count = len([i for i in issues if i.status_name == "Blocked" or i.status.value == "Blocked"])

    completion_rate = (completed_points / total_points * 100) if total_points > 0 else 0

    # Build report
    report = f"## 📊 Sprint Status: {sprint.name}\n\n"
    report += f"**Status**: {sprint.status.value}\n"
    report += f"**Goal**: {sprint.goal or 'No goal set'}\n"
    if sprint.start_date and sprint.end_date:
        days_remaining = (sprint.end_date - datetime.now(timezone.utc)).days
        report += f"**Duration**: {sprint.start_date.strftime('%Y-%m-%d')} to {sprint.end_date.strftime('%Y-%m-%d')}\n"
        report += f"**Days Remaining**: {max(0, days_remaining)}\n"

    report += f"\n### 📈 Progress\n"
    report += f"- **Completion**: {completion_rate:.1f}% ({completed_points}/{total_points} points)\n"
    report += f"- **Total Issues**: {len(issues)}\n"
    report += f"- **In Progress**: {in_progress_count}\n"
    if blocked_count > 0:
        report += f"- **⚠️ Blocked**: {blocked_count}\n"

    return [TextContent(type="text", text=report)]

async def handle_team_workload(args: Dict[str, Any]) -> List[TextContent]:
    """Handle get_team_workload tool call."""
    client = _get_client()
    team_members = args["team_members"]

    report = "## 👥 Team Workload Analysis\n\n"

    for member in team_members:
        try:
            issues = await client.get_assigned_issues(member)
            total_points = sum(issue.story_points for issue in issues if issue.story_points)
            in_progress_count = len([i for i in issues if i.status.value == "In Progress"])

            workload_emoji = "🔴" if total_points > 15 else "🟡" if total_points > 10 else "🟢"

            report += f"### {workload_emoji} {member}\n"
            report += f"- **Total Points**: {total_points}\n"
            report += f"- **Active Issues**: {in_progress_count}\n"
            report += f"- **Total Issues**: {len(issues)}\n\n"

        except Exception as e:
            report += f"### ❌ {member}\n"
            report += f"- **Error**: Could not fetch data ({str(e)})\n\n"

    return [TextContent(type="text", text=report)]

async def handle_standup_report(args: Dict[str, Any]) -> List[TextContent]:
    """Handle generate_standup_report tool call."""
    client = _get_client()
    # Pass board_id if provided
    active_sprint = await client.get_active_sprint(board_id=args.get("board_id"))
    if not active_sprint:
        return [TextContent(type="text", text="No active sprint found for standup report.")]

    issues = await client.get_sprint_issues(active_sprint.id)

    # Categorize issues — use yesterday's date (not today)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    completed_yesterday = [
        i for i in issues
        if i.status.value == "Done" and i.updated_at.date() == yesterday
    ]
    in_progress = [i for i in issues if i.status.value == "In Progress"]
    blocked = [i for i in issues if i.status_name == "Blocked" or i.status.value == "Blocked"]

    report = f"## 🌅 Daily Standup - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
    report += f"**Sprint**: {active_sprint.name}\n\n"

    if completed_yesterday:
        report += "### ✅ Completed Yesterday\n"
        for issue in completed_yesterday:
            assignee = issue.assignee.display_name if issue.assignee else "Unassigned"
            report += f"- **{issue.key}**: {issue.summary} ({assignee})\n"
        report += "\n"

    if in_progress:
        report += "### 🔄 In Progress\n"
        for issue in in_progress:
            assignee = issue.assignee.display_name if issue.assignee else "Unassigned"
            points = f" [{issue.story_points}pts]" if issue.story_points else ""
            report += f"- **{issue.key}**: {issue.summary} ({assignee}){points}\n"
        report += "\n"

    if blocked:
        report += "### ⚠️ Blocked Issues\n"
        for issue in blocked:
            assignee = issue.assignee.display_name if issue.assignee else "Unassigned"
            report += f"- **{issue.key}**: {issue.summary} ({assignee})\n"
        report += "\n"

    # Add quick metrics — guard against division by zero (#1)
    total_points = sum(i.story_points for i in issues if i.story_points)
    completed_points = sum(i.story_points for i in issues if i.story_points and i.status.value == "Done")

    pct = (completed_points / total_points * 100) if total_points > 0 else 0.0

    report += "### 📊 Sprint Metrics\n"
    report += f"- **Progress**: {completed_points}/{total_points} points ({pct:.1f}%)\n"
    report += f"- **Active Issues**: {len(in_progress)}\n"
    if blocked:
        report += f"- **Blocked Issues**: {len(blocked)} ⚠️\n"

    return [TextContent(type="text", text=report)]

async def main():
    """Main entry point for the MCP server."""
    global jira_client

    # Initialize settings and Jira client
    try:
        settings = get_settings()

        # Configure logging to stderr (since stdout is used for MCP protocol)
        logging.basicConfig(
            level=settings.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stderr)]
        )

        jira_client = JiraClient(settings)
        print("Starting MCP Jira server...", file=sys.stderr)
        print("Server is running! Configure your MCP client (like Claude Desktop) to use this server.", file=sys.stderr)
        print("See QUICKSTART.md for connection instructions.", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize: {e}", file=sys.stderr)
        raise

    # Run the MCP server
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        if jira_client:
            await jira_client.close()

if __name__ == "__main__":
    asyncio.run(main())