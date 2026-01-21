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
    import os
    # Try to find .env in current directory or project root
    current_dir = Path(os.getcwd())
    potential_paths = [
        current_dir / ".env",
        Path(__file__).parent.parent.parent / ".env",
        Path("/Users/dford/Projects/mcp-jira/.env") # Fallback to absolute path
    ]
    
    env_path = None
    for path in potential_paths:
        if path.exists():
            env_path = path
            break
            
    if not env_path:
        print("⚠️  No .env file found!", file=sys.stderr)
        print("Please create a .env file with your Jira configuration:", file=sys.stderr)
        print("", file=sys.stderr)
        print("JIRA_URL=https://your-domain.atlassian.net", file=sys.stderr)
        print("JIRA_USERNAME=your.email@domain.com", file=sys.stderr)
        print("JIRA_API_TOKEN=your_api_token", file=sys.stderr)
        print("PROJECT_KEY=PROJ", file=sys.stderr)
        print("DEFAULT_BOARD_ID=123", file=sys.stderr)
        print("", file=sys.stderr)
        print("You can copy .env.example to .env and edit it with your values.", file=sys.stderr)
        return None
    return env_path

if __name__ == "__main__":
    print("Starting MCP Jira Server...", file=sys.stderr)
    
    import os
    print(f"DEBUG: CWD is {os.getcwd()}", file=sys.stderr)
    print(f"DEBUG: Directory contents: {os.listdir()}", file=sys.stderr)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    env_file = check_env_file()
    if not env_file:
        sys.exit(1)
        
    from dotenv import load_dotenv
    print(f"Loading environment from {env_file}", file=sys.stderr)
    load_dotenv(env_file)
    
    try:
        logger.info("Initializing MCP Jira server...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server failed to start: {e}")
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1) 