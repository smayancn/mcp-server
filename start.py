import subprocess
import webbrowser
import time
import os

# Change working directory to MCP root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Start Uvicorn server
process = subprocess.Popen([
    "uvicorn", "main:app",
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

