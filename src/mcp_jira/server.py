"""
FastAPI server implementation for MCP Jira with Scrum Master features.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime

from .jira_client import JiraClient
from .scrum_master import ScrumMaster
from .types import IssueType, Priority, SprintAnalysis, IssueCreate, SprintPlanRequest
from .config import Settings
from .auth import TokenAuth, get_auth_handler

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

# Dependencies
def get_settings():
    return Settings()

def get_jira_client(settings: Settings = Depends(get_settings)):
    return JiraClient(settings)

def get_scrum_master(jira_client: JiraClient = Depends(get_jira_client)):
    return ScrumMaster(jira_client)

# Initialize auth handler
auth_handler = TokenAuth(Settings().api_key)

# API Endpoints
@app.post("/issues")
async def create_issue(
    issue: IssueCreate,
    auth: bool = Depends(auth_handler.verify_token),
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
    auth: bool = Depends(auth_handler.verify_token),
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

@app.get("/sprints/{sprint_id}/analysis")
async def analyze_sprint(
    sprint_id: int,
    auth: bool = Depends(auth_handler.verify_token),
    scrum_master: ScrumMaster = Depends(get_scrum_master)
):
    """Analyze sprint progress and identify risks"""
    try:
        return await scrum_master.analyze_progress(sprint_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/daily-standup")
async def generate_standup_report(
    auth: bool = Depends(auth_handler.verify_token),
    scrum_master: ScrumMaster = Depends(get_scrum_master)
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
    auth: bool = Depends(auth_handler.verify_token),
    scrum_master: ScrumMaster = Depends(get_scrum_master)
):
    """Balance workload across team members for a sprint"""
    try:
        return await scrum_master.balance_workload(sprint_id, team_members)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint - no auth required"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
