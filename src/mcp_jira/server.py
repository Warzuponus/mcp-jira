"""
FastAPI server implementation for MCP Jira with Scrum Master features.
Core server component handling HTTP endpoints and MCP protocol integration.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .jira_client import JiraClient
from .scrum_master import ScrumMaster
from .types import IssueType, Priority, SprintStatus
from .config import Settings

# Initialize FastAPI app
app = FastAPI(
    title="MCP Jira Server",
    description="Model Context Protocol server for Jira with Scrum Master features",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
api_key_header = APIKeyHeader(name="X-API-Key")

# Pydantic models
class IssueCreate(BaseModel):
    summary: str
    description: str
    issue_type: IssueType
    priority: Priority
    story_points: Optional[int] = None
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None
    components: Optional[List[str]] = None

class SprintPlanRequest(BaseModel):
    target_velocity: int
    team_members: List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class SprintAnalysis(BaseModel):
    sprint_id: int
    completion_percentage: float
    remaining_story_points: int
    velocity: float
    risks: List[str]
    recommendations: List[str]
    blocked_issues: List[str]

class StandupReport(BaseModel):
    date: datetime
    completed_yesterday: List[Dict[str, Any]]
    in_progress: List[Dict[str, Any]]
    blocked: List[Dict[str, Any]]
    team_metrics: Dict[str, Any]

# Dependencies
def get_settings():
    return Settings()

def get_jira_client(settings: Settings = Depends(get_settings)):
    return JiraClient(settings)

def get_scrum_master(jira_client: JiraClient = Depends(get_jira_client)):
    return ScrumMaster(jira_client)

async def verify_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
):
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

# Core endpoints
@app.post("/issues", response_model=Dict[str, str])
async def create_issue(
    issue: IssueCreate,
    jira_client: JiraClient = Depends(get_jira_client),
    _: str = Depends(verify_api_key)
):
    """Create a new Jira issue"""
    try:
        result = await jira_client.create_issue(
            summary=issue.summary,
            description=issue.description,
            issue_type=issue.issue_type,
            priority=issue.priority,
            story_points=issue.story_points,
            assignee=issue.assignee,
            labels=issue.labels,
            components=issue.components
        )
        return {"issue_key": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sprints/{sprint_id}/plan", response_model=Dict[str, List[str]])
async def plan_sprint(
    sprint_id: int,
    plan_request: SprintPlanRequest,
    scrum_master: ScrumMaster = Depends(get_scrum_master),
    _: str = Depends(verify_api_key)
):
    """Plan a sprint with automated workload balancing"""
    try:
        recommendations = await scrum_master.plan_sprint(
            sprint_id=sprint_id,
            target_velocity=plan_request.target_velocity,
            team_members=plan_request.team_members,
            start_date=plan_request.start_date,
            end_date=plan_request.end_date
        )
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sprints/{sprint_id}/analysis", response_model=SprintAnalysis)
async def analyze_sprint(
    sprint_id: int,
    scrum_master: ScrumMaster = Depends(get_scrum_master),
    _: str = Depends(verify_api_key)
):
    """Analyze sprint progress and identify risks"""
    try:
        return await scrum_master.analyze_progress(sprint_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/daily-standup", response_model=StandupReport)
async def generate_standup_report(
    scrum_master: ScrumMaster = Depends(get_scrum_master),
    _: str = Depends(verify_api_key)
):
    """Generate daily standup report with team metrics"""
    try:
        return await scrum_master.generate_standup_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sprints/{sprint_id}/workload-balance")
async def balance_sprint_workload(
    sprint_id: int,
    team_members: List[str],
    scrum_master: ScrumMaster = Depends(get_scrum_master),
    _: str = Depends(verify_api_key)
):
    """Balance workload across team members for a sprint"""
    try:
        return await scrum_master.balance_workload(sprint_id, team_members)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sprints/{sprint_id}/risks")
async def identify_sprint_risks(
    sprint_id: int,
    scrum_master: ScrumMaster = Depends(get_scrum_master),
    _: str = Depends(verify_api_key)
):
    """Identify potential risks in the current sprint"""
    try:
        return await scrum_master.identify_risks(sprint_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
