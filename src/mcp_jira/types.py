from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Priority(str, Enum):
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"

class IssueType(str, Enum):
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SUB_TASK = "Sub-task"

class SprintStatus(str, Enum):
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"

class Issue(BaseModel):
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: IssueType
    priority: Optional[Priority] = None
    assignee: Optional[str] = None
    story_points: Optional[float] = None
    sprint: Optional[str] = None
    status: str

class Sprint(BaseModel):
    id: int
    name: str
    status: SprintStatus
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    goal: Optional[str] = None

class SprintMetrics(BaseModel):
    total_points: float
    completed_points: float
    remaining_points: float
    completion_percentage: float
    issues: List[Issue]
