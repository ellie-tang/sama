#!/usr/bin/env python3
"""
Start script for the Vuzix Blade II Face Recognition Web Server
"""

import os
import sys
import logging
from pathlib import Path

def setup_environment():
    """Setup the environment for running the server"""
    # Add the webserver directory to Python path
    webserver_dir = Path(__file__).parent
    sys.path.insert(0, str(webserver_dir))

    # Check for required directories
    required_dirs = [
        webserver_dir / "images" / "uploads",
        webserver_dir.parent / "LLM_Facial_Memory_System"
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            # print(f"Creating directory: {dir_path}")
            print(f"Creating directory: /home/ellie/dev/aiserver/LLM_Facial_Memory_System")
            dir_path.mkdir(parents=True, exist_ok=True)

    # Check for .env file
    env_file = webserver_dir / ".env"
    env_example = webserver_dir / ".env.example"

    if not env_file.exists() and env_example.exists():
        print(f"No .env file found. Please copy {env_example} to {env_file} and configure it.")
        return False

    return True


def main():
    """Main entry point"""
    print("Vuzix Blade II Face Recognition Web Server")
    print("=" * 50)

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    # Import and run the server
    try:
        from main import app, Config
        import uvicorn

        print(f"Starting server on {Config.HOST}:{Config.PORT}")
        print(f"Debug mode: {Config.DEBUG}")
        print(f"Upload directory: /home/ellie/dev/aiserver/webserver/images/uploads")
        print(f"Face system directory: /home/ellie/dev/aiserver/LLM_Facial_Memory_System")
        print("=" * 50)

        uvicorn.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            reload=Config.DEBUG,
            log_level=Config.LOG_LEVEL.lower()
        )

    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements_webserver.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
