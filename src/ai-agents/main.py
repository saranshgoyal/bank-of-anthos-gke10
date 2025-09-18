import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# # Example session service URI (e.g., SQLite)
SESSION_SERVICE_URI = "sqlite:///./sessions.db"

# Point the SQLite database to a writable volume mount in the container.
# SESSION_SERVICE_URI = "sqlite:////data/sessions.db"

# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# You can add more FastAPI routes or configurations below if needed
# Example:
# @app.get("/hello")
# async def read_root():
#     return {"Hello": "World"}

if __name__ == "__main__":
    # Use os.execvp to replace the current process with uvicorn.
    # This is a robust way to run uvicorn in a container.
    # It requires uvicorn to be installed in the environment.
    port = os.environ.get("PORT", "8080")
    # The first argument to execvp is the command to run,
    # and the second is the list of arguments, starting with the command name itself.
    # We use 'python' and '-m uvicorn' to avoid PATH issues with the uvicorn executable.
    args = ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", port]
    os.execvp("python", args)
