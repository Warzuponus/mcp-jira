"""
Type definitions and enums for the MCP Jira server.
Includes all custom types used across the application.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class IssueType(str, Enum):
    """Jira issue types"""
    STORY = "Story"
    BUG = "Bug"
    TASK = "Task"
    EPIC = "Epic"
    SUBTASK = "Sub-task"
    INCIDENT = "Incident"
    SERVICE_REQUEST = "Service Request"


class Priority(str, Enum):
    """Jira priority levels"""
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class SprintStatus(str, Enum):
    """Sprint statuses — values match the Jira Agile REST API responses."""
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"


class IssueStatus(str, Enum):
    """
    Common issue statuses.
    Jira projects can define arbitrary custom statuses, so this enum includes
    a CUSTOM catch-all.  Use IssueStatus.from_name() to safely convert.
    """
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    BLOCKED = "Blocked"
    DONE = "Done"
    CUSTOM = "Custom"

    @classmethod
    def from_name(cls, name: str) -> "IssueStatus":
        """Convert a Jira status name to an IssueStatus, falling back to CUSTOM."""
        for member in cls:
            if member.value == name:
                return member
        return cls.CUSTOM

    # Keep the original status name when the enum value is CUSTOM
    _original_name: str = ""


# Pydantic models for structured data
class TeamMember(BaseModel):
    """Team member information"""
    username: str
    display_name: str
    email: Optional[str] = None
    role: Optional[str] = None
    capacity: Optional[float] = Field(
        default=1.0,
        description="Capacity as percentage (1.0 = 100%)"
    )


class Issue(BaseModel):
    """Jira issue details"""
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: IssueType
    priority: Priority
    status: IssueStatus
    status_name: str = ""  # original Jira status name (useful when status == CUSTOM)
    assignee: Optional[TeamMember] = None
    story_points: Optional[float] = None
    labels: List[str] = []
    components: List[str] = []
    created_at: datetime
    updated_at: datetime
    blocked_by: List[str] = []
    blocks: List[str] = []


class Sprint(BaseModel):
    """Sprint information"""
    id: int
    name: str
    goal: Optional[str] = None
    status: SprintStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    completed_points: float = 0
    total_points: float = 0
    team_members: List[TeamMember] = []


# Custom exceptions
class JiraError(Exception):
    """Base exception for Jira-related errors"""
    pass
