from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from .jira_client import JiraClient
from .scrum_master import ScrumMaster
from .types import IssueType, Priority
from .config import Settings

app = FastAPI(
    title="MCP Jira Server",
    description="Model Context Protocol server for Jira with Scrum Master features",
    version="1.0.0"
)

# Pydantic models for request/response
class IssueCreate(BaseModel):
    summary: str
    description: str
    issue_type: IssueType
    priority: Priority
    story_points: Optional[int] = None
    assignee: Optional[str] = None

class SprintPlanRequest(BaseModel):
    target_velocity: int
    team_members: List[str]

class SprintAnalysis(BaseModel):
    completion_percentage: float
    remaining_story_points: int
    risks: List[str]
    recommendations: List[str]

# Dependencies
def get_jira_client():
    settings = Settings()
    return JiraClient(settings)

def get_scrum_master(jira_client: JiraClient = Depends(get_jira_client)):
    return ScrumMaster(jira_client)

# Core endpoints
@app.post("/issues", response_model=dict)
async def create_issue(
    issue: IssueCreate,
    jira_client: JiraClient = Depends(get_jira_client)
):
    """Create a new Jira issue"""
    try:
        result = await jira_client.create_issue(
            summary=issue.summary,
            description=issue.description,
            issue_type=issue.issue_type,
            priority=issue.priority,
            story_points=issue.story_points,
            assignee=issue.assignee
        )
        return {"issue_key": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sprints/{sprint_id}/plan")
async def plan_sprint(
    sprint_id: int,
    plan_request: SprintPlanRequest,
    scrum_master: ScrumMaster = Depends(get_scrum_master)
):
    """Plan a sprint with automated workload balancing"""
    try:
        recommendations = await scrum_master.plan_sprint(
            sprint_id=sprint_id,
            target_velocity=plan_request.target_velocity,
            team_members=plan_request.team_members
        )
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sprints/{sprint_id}/analysis", response_model=SprintAnalysis)
async def analyze_sprint(
    sprint_id: int,
    scrum_master: ScrumMaster = Depends(get_scrum_master)
):
    """Analyze sprint progress and identify risks"""
    try:
        return await scrum_master.analyze_progress(sprint_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/daily-standup")
async def generate_standup_report(
    scrum_master: ScrumMaster = Depends(get_scrum_master)
):
    """Generate daily standup report"""
    try:
        return await scrum_master.generate_standup_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
