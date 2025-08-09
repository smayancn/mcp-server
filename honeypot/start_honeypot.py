#!/usr/bin/env python3
"""
MCP Honeypot Launcher
Starts the honeypot on port 8001 to capture attacks
"""

import subprocess
import webbrowser
import time
import os
from pathlib import Path

def main():
    # Change to honeypot directory
    honeypot_dir = Path(__file__).parent
    os.chdir(honeypot_dir)
    
    print("🍯 Starting MCP Honeypot...")
    print("=" * 50)
    print("🎯 Honeypot URL: http://localhost:8001")
    print("🚨 Admin Panel: http://localhost:8001/honeypot/admin")
    print("🔒 Real Server: http://localhost:8000 (your actual files)")
    print("=" * 50)
    print()
    print("⚠️  SECURITY NOTE:")
    print("   - The honeypot logs all interactions")
    print("   - Only access admin panel from localhost")
    print("   - Monitor logs for real security threats")
    print()
    
    try:
        # Start the honeypot server
        process = subprocess.Popen([
            "python3", "honeypot_main.py"
        ])
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Open admin panel (only if running locally)
        try:
            webbrowser.open("http://localhost:8001/honeypot/admin")
        except:
            pass
        
        print("✅ Honeypot is running!")
        print("Press Ctrl+C to stop...")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping honeypot...")
        process.terminate()
        process.wait()
        print("✅ Honeypot stopped safely")
    
    except Exception as e:
        print(f"❌ Error starting honeypot: {e}")

if __name__ == "__main__":
    main()
