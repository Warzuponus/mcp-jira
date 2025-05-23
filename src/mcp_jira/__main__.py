#!/usr/bin/env python3
"""
Main entry point for mcp-jira.
Allows running with `python -m mcp_jira`.
"""

import asyncio
import sys
import logging
from pathlib import Path

from .simple_mcp_server import main
from .config import get_settings, initialize_logging

def setup_logging():
    """Set up logging configuration."""
    try:
        settings = get_settings()
        initialize_logging(settings)
    except Exception as e:
        # Fallback logging if config fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.getLogger(__name__).warning(f"Failed to load settings: {e}")

def check_env_file():
    """Check if .env file exists and provide helpful guidance."""
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  No .env file found!")
        print("Please create a .env file with your Jira configuration:")
        print("")
        print("JIRA_URL=https://your-domain.atlassian.net")
        print("JIRA_USERNAME=your.email@domain.com")
        print("JIRA_API_TOKEN=your_api_token")
        print("PROJECT_KEY=PROJ")
        print("DEFAULT_BOARD_ID=123")
        print("")
        print("You can copy .env.example to .env and edit it with your values.")
        return False
    return True

if __name__ == "__main__":
    print("🚀 Starting MCP Jira Server...")
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if not check_env_file():
        sys.exit(1)
    
    try:
        logger.info("Initializing MCP Jira server...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server failed to start: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1) 