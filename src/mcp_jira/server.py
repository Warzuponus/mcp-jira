from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="MCP Jira Server")