from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .jira_client import JiraClient
from .types import Issue, Sprint, SprintMetrics, Priority, IssueType

class ScrumMaster:
    def __init__(self):
        self.jira = JiraClient()

    async def plan_sprint(self, sprint_id: int, target_velocity: float) -> Dict[str, Any]:
        """Plan and provide recommendations for sprint planning"""
        metrics = await self.jira.get_sprint_metrics(sprint_id)
        
        analysis = {
            "recommendations": [],
            "workload_distribution": {},
            "risks": [],
            "capacity_analysis": {
                "total_points": metrics.total_points,
                "target_velocity": target_velocity,
                "variance": metrics.total_points - target_velocity
            }
        }

        # Analyze workload distribution
        for issue in metrics.issues:
            if issue.assignee:
                points = issue.story_points or 0
                if issue.assignee not in analysis["workload_distribution"]:
                    analysis["workload_distribution"][issue.assignee] = {
                        "points": 0,
                        "issues": []
                    }
                analysis["workload_distribution"][issue.assignee]["points"] += points
                analysis["workload_distribution"][issue.assignee]["issues"].append({
                    "key": issue.key,
                    "points": points,
                    "summary": issue.summary
                })

        # Generate recommendations
        if metrics.total_points > target_velocity * 1.2:
            analysis["recommendations"].append({
                "type": "overcommitment",
                "severity": "high",
                "message": f"Sprint is overcommitted by {metrics.total_points - target_velocity} points",
                "action": "Review and potentially remove lower priority items",
                "details": {
                    "current_points": metrics.total_points,
                    "target_points": target_velocity,
                    "overage": metrics.total_points - target_velocity
                }
            })

        # Check workload balance
        team_size = len(analysis["workload_distribution"])
        if team_size > 0:
            avg_points = target_velocity / team_size
            for assignee, workload in analysis["workload_distribution"].items():
                if workload["points"] > avg_points * 1.3:
                    analysis["recommendations"].append({
                        "type": "workload_imbalance",
                        "severity": "medium",
                        "message": f"{assignee} is overloaded with {workload['points']} points",
                        "action": "Redistribute work to team members with less load",
                        "details": {
                            "assignee": assignee,
                            "current_points": workload["points"],
                            "team_average": avg_points,
                            "affected_issues": workload["issues"]
                        }
                    })

        # Story point distribution analysis
        story_points_distribution = {}
        for issue in metrics.issues:
            points = issue.story_points or 0
            if points not in story_points_distribution:
                story_points_distribution[points] = 0
            story_points_distribution[points] += 1

        if 13 in story_points_distribution or 21 in story_points_distribution:
            analysis["recommendations"].append({
                "type": "large_stories",
                "severity": "medium",
                "message": "Some stories might be too large for a single sprint",
                "action": "Consider breaking down stories larger than 8 points",
                "details": {
                    "distribution": story_points_distribution
                }
            })

        return analysis

    async def analyze_progress(self, sprint_id: int) -> Dict[str, Any]:
        """Analyze sprint progress and identify risks"""
        metrics = await self.jira.get_sprint_metrics(sprint_id)
        sprint = await self.jira.get_sprint(sprint_id)
        
        analysis = {
            "metrics": {
                "total_points": metrics.total_points,
                "completed_points": metrics.completed_points,
                "remaining_points": metrics.remaining_points,
                "completion_percentage": metrics.completion_percentage,
                "time_remaining": self._calculate_time_remaining(sprint)
            },
            "risks": [],
            "recommendations": [],
            "status_distribution": {},
            "blocked_issues": []
        }

        # Status distribution analysis
        for issue in metrics.issues:
            if issue.status not in analysis["status_distribution"]:
                analysis["status_distribution"][issue.status] = {
                    "count": 0,
                    "points": 0,
                    "issues": []
                }
            status_data = analysis["status_distribution"][issue.status]
            status_data["count"] += 1
            status_data["points"] += issue.story_points or 0
            status_data["issues"].append({
                "key": issue.key,
                "summary": issue.summary,
                "points": issue.story_points
            })

            # Track blocked issues
            if issue.status.lower() in ['blocked', 'impediment']:
                analysis["blocked_issues"].append({
                    "key": issue.key,
                    "summary": issue.summary,
                    "points": issue.story_points,
                    "assignee": issue.assignee
                })

        # Calculate ideal burndown
        total_days = self._calculate_sprint_length(sprint)
        if total_days > 0:
            days_elapsed = self._calculate_days_elapsed(sprint)
            ideal_completion = (days_elapsed / total_days) * 100
            
            if metrics.completion_percentage < ideal_completion - 20:
                analysis["risks"].append({
                    "type": "behind_schedule",
                    "severity": "high",
                    "message": f"Sprint is significantly behind schedule",
                    "details": {
                        "current_completion": metrics.completion_percentage,
                        "expected_completion": ideal_completion,
                        "variance": ideal_completion - metrics.completion_percentage
                    }
                })

        # Analyze blocked issues impact
        if analysis["blocked_issues"]:
            blocked_points = sum(issue["points"] or 0 for issue in analysis["blocked_issues"])
            if blocked_points > metrics.total_points * 0.2:
                analysis["risks"].append({
                    "type": "blocked_work",
                    "severity": "high",
                    "message": f"Large amount of work is blocked ({blocked_points} points)",
                    "action": "Immediate scrum master intervention needed",
                    "details": {
                        "blocked_points": blocked_points,
                        "blocked_percentage": (blocked_points / metrics.total_points) * 100,
                        "blocked_issues": analysis["blocked_issues"]
                    }
                })

        return analysis

    async def suggest_priority_updates(self, sprint_id: int) -> List[Dict[str, Any]]:
        """Suggest priority updates based on sprint progress"""
        metrics = await self.jira.get_sprint_metrics(sprint_id)
        suggestions = []

        for issue in metrics.issues:
            # Suggest priority increases for blocked issues
            if issue.status.lower() in ['blocked', 'impediment'] and issue.priority != Priority.HIGHEST:
                suggestions.append({
                    "issue_key": issue.key,
                    "type": "priority_increase",
                    "current_priority": issue.priority,
                    "suggested_priority": Priority.HIGHEST,
                    "reason": "Blocked issue impacting sprint progress",
                    "action": {
                        "field": "priority",
                        "value": Priority.HIGHEST.value
                    }
                })

            # Suggest priority increases for high-point items not started
            if (issue.story_points or 0) > 5 and issue.status.lower() in ['to do', 'open']:
                suggestions.append({
                    "issue_key": issue.key,
                    "type": "priority_increase",
                    "current_priority": issue.priority,
                    "suggested_priority": Priority.HIGH,
                    "reason": "High-effort item not started",
                    "action": {
                        "field": "priority",
                        "value": Priority.HIGH.value
                    }
                })

        return suggestions

    async def get_daily_standup_report(self, sprint_id: int) -> Dict[str, Any]:
        """Generate a daily standup report"""
        metrics = await self.jira.get_sprint_metrics(sprint_id)
        yesterday_cutoff = datetime.now() - timedelta(days=1)
        
        report = {
            "date": datetime.now().isoformat(),
            "sprint_metrics": {
                "completion_percentage": metrics.completion_percentage,
                "remaining_points": metrics.remaining_points
            },
            "team_updates": {},
            "blockers": [],
            "priorities": []
        }

        # Gather team member updates
        for issue in metrics.issues:
            if issue.assignee:
                if issue.assignee not in report["team_updates"]:
                    report["team_updates"][issue.assignee] = {
                        "completed": [],
                        "in_progress": [],
                        "planned": []
                    }
                
                updates = report["team_updates"][issue.assignee]
                issue_info = {
                    "key": issue.key,
                    "summary": issue.summary,
                    "points": issue.story_points
                }

                if issue.status.lower() in ['done', 'completed']:
                    updates["completed"].append(issue_info)
                elif issue.status.lower() in ['in progress']:
                    updates["in_progress"].append(issue_info)
                elif issue.status.lower() in ['to do', 'open']:
                    updates["planned"].append(issue_info)

                if issue.status.lower() in ['blocked', 'impediment']:
                    report["blockers"].append({
                        "key": issue.key,
                        "summary": issue.summary,
                        "assignee": issue.assignee,
                        "points": issue.story_points
                    })

        # Identify top priorities
        high_priority_issues = [
            issue for issue in metrics.issues
            if issue.priority in [Priority.HIGHEST, Priority.HIGH]
            and issue.status.lower() not in ['done', 'completed']
        ]
        report["priorities"] = [
            {
                "key": issue.key,
                "summary": issue.summary,
                "assignee": issue.assignee,
                "points": issue.story_points,
                "status": issue.status
            }
            for issue in high_priority_issues
        ]

        return report

    def _calculate_time_remaining(self, sprint: Sprint) -> Optional[int]:
        """Calculate remaining days in sprint"""
        if sprint.end_date:
            end_date = datetime.fromisoformat(sprint.end_date.replace('Z', '+00:00'))
            remaining = end_date - datetime.now(end_date.tzinfo)
            return max(0, remaining.days)
        return None

    def _calculate_sprint_length(self, sprint: Sprint) -> int:
        """Calculate total sprint length in days"""
        if sprint.start_date and sprint.end_date:
            start = datetime.fromisoformat(sprint.start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(sprint.end_date.replace('Z', '+00:00'))
            return (end - start).days
        return 0

    def _calculate_days_elapsed(self, sprint: Sprint) -> int:
        """Calculate days elapsed in sprint"""
        if sprint.start_date:
            start = datetime.fromisoformat(sprint.start_date.replace('Z', '+00:00'))
            elapsed = datetime.now(start.tzinfo) - start
            return elapsed.days
        return 0
