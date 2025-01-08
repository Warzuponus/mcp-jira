# MCP Jira with Scrum Master Features

A Python-based Model Context Protocol (MCP) server for Jira that includes enhanced Scrum Master and Executive Assistant capabilities.

## Features

### Core MCP Features
- Jira issue creation and management
- Sprint tracking and metrics
- Resource and function-based MCP protocol

### Scrum Master Features
- Automated sprint planning
- Progress analysis and tracking
- Workload balancing
- Risk identification
- Priority management

### Executive Assistant Features
- Daily standup report generation
- Sprint metrics and analytics
- Team performance tracking
- Blocking issue detection

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Configure environment variables in `.env`:
   ```env
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your.email@domain.com
   JIRA_API_TOKEN=your_api_token
   PROJECT_KEY=PROJ
   DEFAULT_BOARD_ID=123
   ```

## Usage

1. Start the server:
   ```bash
   uvicorn mcp_jira.server:app --reload
   ```

2. Access the API documentation at `http://localhost:8000/docs`

## API Examples

### Create Issue
```python
await client.create_issue(
    summary="Implement feature X",
    description="Detailed description",
    issue_type=IssueType.STORY,
    priority=Priority.HIGH,
    story_points=5
)
```

### Plan Sprint
```python
recommendations = await client.plan_sprint(
    sprint_id=123,
    target_velocity=30
)
```

### Analyze Progress
```python
analysis = await client.analyze_progress(sprint_id=123)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file
