#!/usr/bin/env python3
"""
Startup script for Email Processor FastAPI Server
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main startup function"""
    print("Starting Email Processor FastAPI Server...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Warning: .env file not found!")
        print("   Please copy env.example to .env and configure your settings")
        print("   Using default configuration...")
    
    # Check if models directory exists
    models_dir = Path("./models")
    if not models_dir.exists():
        print("Creating models directory...")
        models_dir.mkdir(exist_ok=True)
    
    # Check if logs directory exists
    logs_dir = Path("./logs")
    if not logs_dir.exists():
        print("Creating logs directory...")
        logs_dir.mkdir(exist_ok=True)
    
    # Check if emails_backup directory exists
    backup_dir = Path("./emails_backup")
    if not backup_dir.exists():
        print("Creating emails_backup directory...")
        backup_dir.mkdir(exist_ok=True)
    
    print("Environment setup complete!")
    print("Starting FastAPI server...")
    
    # Import and run the FastAPI app
    try:
        from app.api import app
        import uvicorn
        
        uvicorn.run(
            "app.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("   Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
