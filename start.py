import subprocess
import webbrowser
import time
import os
import sys
from pathlib import Path

def main():
    # Change working directory to MCP root
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting MCP Media Center System...")
    print("=" * 60)
    
    # Try to use venv uvicorn first, fall back to system uvicorn
    venv_uvicorn = script_dir / "venv" / "bin" / "uvicorn"
    if venv_uvicorn.exists():
        uvicorn_cmd = str(venv_uvicorn)
    else:
        uvicorn_cmd = "uvicorn"
    
    processes = []
    
    try:
        # Start the real MCP server (port 8000)
        print("📁 Starting Real MCP File Server on port 8000...")
        try:
            real_server = subprocess.Popen([
                uvicorn_cmd, "main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ])
        except FileNotFoundError:
            print("   Fallback to python -m uvicorn...")
            real_server = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "main:app",
                "--host", "0.0.0.0", 
                "--port", "8000",
                "--reload"
            ])
        
        processes.append(real_server)
        print("✅ Real server started")
        
        # Start the honeypot server (port 8001) 
        print("🍯 Starting Security Honeypot on port 8001...")
        honeypot_dir = script_dir / "honeypot"
        honeypot_server = subprocess.Popen([
            sys.executable, "honeypot_main.py"
        ], cwd=honeypot_dir)
        
        processes.append(honeypot_server)
        print("✅ Honeypot started")
        
        # Wait for servers to start
        time.sleep(3)
        
        print("=" * 60)
        print("🌐 SYSTEM READY:")
        print("   Real File Server:  http://localhost:8000")
        print("   Security Honeypot: http://localhost:8001") 
        print("   Admin Dashboard:   http://localhost:8001/honeypot/admin")
        print("=" * 60)
        print("🔐 Login: admin / admin")
        print("⚠️  Attackers will be captured by the honeypot!")
        print()
        
        # Open the real MCP server in browser
        webbrowser.open("http://localhost:8000")
        
        print("✅ Both servers running. Press Ctrl+C to stop...")
        
        # Wait for all processes
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        for process in processes:
            process.terminate()
        
        # Wait for clean shutdown
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ All servers stopped safely")
    
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        for process in processes:
            process.terminate()

if __name__ == "__main__":
    main()

