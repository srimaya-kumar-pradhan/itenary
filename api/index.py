import sys
import os

# Resolve absolute paths for the root and backend folders
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Add paths to sys.path so backend imports resolve successfully
if root_dir not in sys.path:
    sys.path.append(root_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Set the current working directory to the project root for local file paths (vector_db, dataset)
os.chdir(root_dir)

# Expose the FastAPI app for Vercel Serverless Functions
from backend.main import app
