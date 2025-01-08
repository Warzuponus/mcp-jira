"""
Type definitions and enums for the MCP Jira server.
Includes all custom types used across the application.
"""

from enum import Enum, auto
from typing import List, Dict, Any, Optional
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
    """Sprint statuses"""
    PLANNING = "Planning"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class IssueStatus(str, Enum):
    """Issue statuses"""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    BLOCKED = "Blocked"
    DONE = "Done"

class RiskLevel(str, Enum):
    """Risk levels for sprint analysis"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class RiskType(str, Enum):
    """Types of risks that can be identified"""
    SCOPE_CREEP = "Scope Creep"
    RESOURCE_CONSTRAINT = "Resource Constraint"
    TECHNICAL_DEBT = "Technical Debt"
    DEPENDENCY_RISK = "Dependency Risk"
    VELOCITY_RISK = "Velocity Risk"
    CAPACITY_RISK = "Capacity Risk"

# Pydantic models for structured data
class TeamMember(BaseModel):
    """Team member information"""
    username: str
    display_name: str
    email: Optional[str]
    role: Optional[str]
    capacity: Optional[float] = Field(
        default=1.0,
        description="Capacity as percentage (1.0 = 100%)"
    )

class Issue(BaseModel):
    """Jira issue details"""
    key: str
    summary: str
    description: Optional[str]
    issue_type: IssueType
    priority: Priority
    status: IssueStatus
    assignee: Optional[TeamMember]
    story_points: Optional[float]
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
    goal: Optional[str]
    status: SprintStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    completed_points: float = 0
    total_points: float = 0
    team_members: List[TeamMember] = []

class Risk(BaseModel):
    """Risk assessment details"""
    type: RiskType
    level: RiskLevel
    description: str
    impact: str
    mitigation: Optional[str]
    affected_issues: List[str] = []

class SprintMetrics(BaseModel):
    """Sprint performance metrics"""
    velocity: float
    completion_rate: float
    average_cycle_time: float
    blocked_issues_count: int
    scope_changes: int
    team_capacity: float
    burndown_ideal: Dict[str, float]
    burndown_actual: Dict[str, float]

class WorkloadBalance(BaseModel):
    """Workload distribution information"""
    team_member: TeamMember
    assigned_points: float
    issue_count: int
    current_capacity: float
    recommendations: List[str]

class DailyStandupItem(BaseModel):
    """Individual standup update"""
    issue_key: str
    summary: str
    status: IssueStatus
    assignee: str
    blocked_reason: Optional[str]
    notes: Optional[str]
    time_spent: Optional[float]

# Custom exceptions
class JiraError(Exception):
    """Base exception for Jira-related errors"""
    pass

class SprintError(Exception):
    """Base exception for Sprint-related errors"""
    pass

class ConfigError(Exception):
    """Base exception for configuration errors"""
    pass

# Type aliases for complex types
SprintPlanningResult = Dict[str, List[Issue]]
WorkloadDistribution = Dict[str, WorkloadBalance]
RiskAssessment = List[Risk]
TeamCapacityMap = Dict[str, float]
