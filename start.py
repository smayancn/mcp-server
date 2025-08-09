import subprocess
import webbrowser
import time
import os
import sys
from pathlib import Path

# Change working directory to MCP root
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Try to use venv uvicorn first, fall back to system uvicorn
venv_uvicorn = script_dir / "venv" / "bin" / "uvicorn"
if venv_uvicorn.exists():
    uvicorn_cmd = str(venv_uvicorn)
else:
    # Try system uvicorn or use python -m uvicorn
    uvicorn_cmd = "uvicorn"

try:
    # Start Uvicorn server
    process = subprocess.Popen([
        uvicorn_cmd, "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
except FileNotFoundError:
    # Fallback to python -m uvicorn
    print("uvicorn command not found, trying python -m uvicorn...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])

# Wait a moment for the server to start
time.sleep(2)

# Open the MCP dashboard in the default browser
webbrowser.open("http://localhost:8000")

# Wait until the process is killed manually
try:
    process.wait()
except KeyboardInterrupt:
    process.terminate()

