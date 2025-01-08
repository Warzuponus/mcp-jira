"""
ScrumMaster class implementation for MCP Jira.
Handles sprint planning, analysis, risk assessment, and team management.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from statistics import mean, stdev

from .jira_client import JiraClient
from .types import (
    Sprint, Issue, TeamMember, Risk, SprintMetrics, 
    WorkloadBalance, RiskType, RiskLevel, IssueStatus,
    SprintStatus, DailyStandupItem
)

logger = logging.getLogger(__name__)

class ScrumMaster:
    def __init__(self, jira_client: JiraClient):
        self.jira = jira_client
        self.RISK_THRESHOLDS = {
            'velocity_variance': 0.2,  # 20% variance from historical velocity
            'workload_imbalance': 0.3,  # 30% difference between team members
            'blocking_issues': 2,  # More than 2 blocking issues is high risk
            'scope_change': 0.15,  # 15% scope change is concerning
        }

    async def plan_sprint(
        self,
        sprint_id: int,
        target_velocity: float,
        team_members: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[str]:
        """Plan a sprint with automated workload balancing."""
        recommendations = []
        
        # Get sprint and team data
        sprint = await self.jira.get_sprint(sprint_id)
        team_capacities = await self._calculate_team_capacities(team_members)
        backlog_issues = await self.jira.get_backlog_issues()
        
        # Calculate sprint capacity
        total_capacity = sum(team_capacities.values())
        ideal_points_per_member = target_velocity / len(team_members)
        
        # Prioritize and select issues
        selected_issues = []
        current_points = 0
        
        for issue in backlog_issues:
            if current_points >= target_velocity:
                break
                
            if issue.story_points and current_points + issue.story_points <= target_velocity * 1.1:
                selected_issues.append(issue)
                current_points += issue.story_points
                
        # Generate recommendations
        if current_points < target_velocity * 0.9:
            recommendations.append(f"Warning: Selected issues ({current_points} points) are below target velocity ({target_velocity} points)")
            
        if len(selected_issues) > len(team_members) * 3:
            recommendations.append("Warning: High number of issues per team member may impact focus")
            
        # Balance workload
        workload = await self.balance_workload(sprint_id, team_members)
        recommendations.extend(self._generate_workload_recommendations(workload))
        
        return recommendations

    async def analyze_progress(self, sprint_id: int) -> SprintMetrics:
        """Analyze sprint progress and generate metrics."""
        sprint = await self.jira.get_sprint(sprint_id)
        sprint_issues = await self.jira.get_sprint_issues(sprint_id)
        
        # Calculate core metrics
        completed_points = sum(issue.story_points for issue in sprint_issues 
                             if issue.status == IssueStatus.DONE and issue.story_points)
        total_points = sum(issue.story_points for issue in sprint_issues if issue.story_points)
        
        completion_rate = completed_points / total_points if total_points > 0 else 0
        
        # Calculate velocity and variance
        historical_velocities = await self._get_historical_velocities(3)  # Last 3 sprints
        current_velocity = completed_points / ((sprint.end_date - sprint.start_date).days / 7)
        
        metrics = SprintMetrics(
            velocity=current_velocity,
            completion_rate=completion_rate,
            average_cycle_time=await self._calculate_cycle_time(sprint_issues),
            blocked_issues_count=len([i for i in sprint_issues if i.status == IssueStatus.BLOCKED]),
            scope_changes=await self._count_scope_changes(sprint_id),
            team_capacity=await self._calculate_team_capacity(sprint_id),
            burndown_ideal=self._generate_ideal_burndown(sprint, total_points),
            burndown_actual=await self._generate_actual_burndown(sprint_id)
        )
        
        return metrics

    async def identify_risks(self, sprint_id: int) -> List[Risk]:
        """Identify potential risks in the current sprint."""
        risks = []
        sprint = await self.jira.get_sprint(sprint_id)
        issues = await self.jira.get_sprint_issues(sprint_id)
        
        # Analyze velocity risk
        velocity_risk = await self._assess_velocity_risk(sprint_id)
        if velocity_risk:
            risks.append(velocity_risk)
            
        # Analyze dependency risks
        dependency_risks = await self._assess_dependency_risks(issues)
        risks.extend(dependency_risks)
        
        # Analyze capacity risks
        capacity_risk = await self._assess_capacity_risk(sprint_id)
        if capacity_risk:
            risks.append(capacity_risk)
            
        # Analyze scope risks
        scope_risk = await self._assess_scope_risk(sprint_id)
        if scope_risk:
            risks.append(scope_risk)
            
        return risks

    async def generate_standup_report(self) -> Dict[str, List[DailyStandupItem]]:
        """Generate daily standup report with team metrics."""
        active_sprint = await self.jira.get_active_sprint()
        if not active_sprint:
            raise ValueError("No active sprint found")
            
        issues = await self.jira.get_sprint_issues(active_sprint.id)
        
        # Categorize issues
        completed_yesterday = []
        in_progress = []
        blocked = []
        
        yesterday = datetime.now() - timedelta(days=1)
        
        for issue in issues:
            if issue.status == IssueStatus.DONE and issue.updated_at.date() == yesterday.date():
                completed_yesterday.append(self._create_standup_item(issue))
            elif issue.status == IssueStatus.IN_PROGRESS:
                in_progress.append(self._create_standup_item(issue))
            elif issue.status == IssueStatus.BLOCKED:
                blocked.append(self._create_standup_item(issue))
                
        return {
            "completed_yesterday": completed_yesterday,
            "in_progress": in_progress,
            "blocked": blocked,
            "metrics": await self._get_daily_metrics(active_sprint.id)
        }

    # Helper methods
    async def _calculate_team_capacities(self, team_members: List[str]) -> Dict[str, float]:
        """Calculate capacity for each team member."""
        capacities = {}
        for member in team_members:
            member_issues = await self.jira.get_assigned_issues(member)
            current_workload = sum(issue.story_points for issue in member_issues if issue.story_points)
            capacities[member] = max(0, 1 - (current_workload / 20))  # Assuming 20 points is full capacity
        return capacities

    async def _calculate_cycle_time(self, issues: List[Issue]) -> float:
        """Calculate average cycle time for completed issues."""
        cycle_times = []
        for issue in issues:
            if issue.status == IssueStatus.DONE:
                history = await self.jira.get_issue_history(issue.key)
                in_progress_time = sum(
                    (entry['to_date'] - entry['from_date']).days
                    for entry in history
                    if entry['status'] == IssueStatus.IN_PROGRESS
                )
                cycle_times.append(in_progress_time)
        return mean(cycle_times) if cycle_times else 0

    def _create_standup_item(self, issue: Issue) -> DailyStandupItem:
        """Create a standup item from an issue."""
        return DailyStandupItem(
            issue_key=issue.key,
            summary=issue.summary,
            status=issue.status,
            assignee=issue.assignee.display_name if issue.assignee else "Unassigned",
            blocked_reason=next((block.description for block in issue.blocked_by), None),
            time_spent=None  # TODO: Implement time tracking
        )

    # Additional helper methods would go here...
