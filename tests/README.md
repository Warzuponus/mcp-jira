# Tests

This directory contains the test suite for the MCP Jira server.

## Prerequisites

Ensure you have installed the development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_jira_client.py
```

## Structure

- `conftest.py`: Shared fixtures and configuration (mocks, test data).
- `test_jira_client.py`: Tests for the Jira API client.
- `test_simple_mcp_server.py`: Tests for the MCP server and tool handlers.
