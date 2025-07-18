#!/usr/bin/env python3
"""
Legal ASI - Standalone API Runner
Runs FastAPI without Docker dependencies for testing
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock environment variables for standalone testing
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")  # Use SQLite for testing
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("TESTING", "true")

def run_standalone_api():
    """Run API in standalone mode for testing"""
    try:
        print("🚀 Starting Legal ASI API in standalone mode...")
        print("   No external dependencies (DB, Redis) required for basic testing")
        print("   API will be available at: http://localhost:8000")
        print("   Press Ctrl+C to stop")
        print()
        
        # Import and run the FastAPI app
        from api.main import app
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False  # Disable reload for testing
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from project root")
        return False
    except KeyboardInterrupt:
        print("\n👋 API stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        return False

if __name__ == "__main__":
    success = run_standalone_api()
    sys.exit(0 if success else 1) 