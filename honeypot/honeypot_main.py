from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import hashlib
import os

app = FastAPI(title="MCP Honeypot", description="Security Honeypot for MCP File Server")

# Honeypot specific paths
HONEYPOT_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=HONEYPOT_DIR / "static"), name="static")
templates = Jinja2Templates(directory=HONEYPOT_DIR / "templates")

# Initialize database
def init_database():
    """Initialize SQLite database for logging attacks"""
    db_path = HONEYPOT_DIR / "database" / "honeypot.db"
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables for logging different types of attacks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            username TEXT,
            password TEXT,
            user_agent TEXT,
            session_id TEXT,
            success BOOLEAN DEFAULT FALSE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            path TEXT,
            method TEXT,
            user_agent TEXT,
            session_id TEXT,
            headers TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            ip_address TEXT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_requests INTEGER DEFAULT 0,
            attack_type TEXT,
            risk_level INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize on startup
init_database()

def log_attack(attack_type: str, data: dict, request: Request):
    """Log attack data to database"""
    db_path = HONEYPOT_DIR / "database" / "honeypot.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Generate session ID based on IP + User Agent
    session_data = f"{data.get('ip_address', '')}:{data.get('user_agent', '')}"
    session_id = hashlib.md5(session_data.encode()).hexdigest()[:12]
    
    # Update session tracking
    cursor.execute("""
        INSERT OR REPLACE INTO attack_sessions 
        (session_id, ip_address, last_activity, total_requests, attack_type)
        VALUES (?, ?, CURRENT_TIMESTAMP, 
                COALESCE((SELECT total_requests FROM attack_sessions WHERE session_id = ?), 0) + 1,
                ?)
    """, (session_id, data.get('ip_address'), session_id, attack_type))
    
    data['session_id'] = session_id
    
    if attack_type == "login_attempt":
        cursor.execute("""
            INSERT INTO login_attempts 
            (ip_address, username, password, user_agent, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get('ip_address'),
            data.get('username'),
            data.get('password'),
            data.get('user_agent'),
            session_id
        ))
    
    elif attack_type == "page_visit":
        cursor.execute("""
            INSERT INTO page_visits 
            (ip_address, path, method, user_agent, session_id, headers)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('ip_address'),
            data.get('path'),
            data.get('method'),
            data.get('user_agent'),
            session_id,
            json.dumps(dict(request.headers))
        ))
    
    conn.commit()
    conn.close()
    
    # Also log to file for immediate analysis
    log_file = HONEYPOT_DIR / "logs" / f"honeypot_{datetime.now().strftime('%Y%m%d')}.log"
    log_file.parent.mkdir(exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": attack_type,
        "session_id": session_id,
        **data
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Log page visit
    log_attack("page_visit", {
        "ip_address": client_ip,
        "path": str(request.url.path),
        "method": request.method,
        "user_agent": user_agent
    }, request)
    
    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def honeypot_login(request: Request):
    """Fake login page that looks exactly like the real MCP"""
    return templates.TemplateResponse("fake_login.html", {"request": request})

@app.post("/login")
async def fake_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Capture login attempts"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Log the login attempt
    log_attack("login_attempt", {
        "ip_address": client_ip,
        "username": username,
        "password": password,
        "user_agent": user_agent
    }, request)
    
    # Always return "invalid credentials" to keep them trying
    return templates.TemplateResponse("fake_login.html", {
        "request": request,
        "error": "Invalid username or password. Please try again.",
        "username": username  # Keep username filled for convenience
    })

@app.get("/dashboard")
async def fake_dashboard(request: Request):
    """Fake dashboard that looks real but logs everything"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    log_attack("dashboard_access", {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "note": "Attacker accessed fake dashboard"
    }, request)
    
    return templates.TemplateResponse("fake_dashboard.html", {"request": request})

@app.get("/api/diagnostics")
async def fake_api_diagnostics(request: Request):
    """Fake API endpoint that returns believable but fake data"""
    client_ip = request.client.host
    
    log_attack("api_access", {
        "ip_address": client_ip,
        "endpoint": "/api/diagnostics",
        "user_agent": request.headers.get("user-agent", "Unknown")
    }, request)
    
    # Return fake but believable system stats
    return {
        "cpu": {"usage": 23.4},
        "memory": {
            "used": 6.2,
            "total": 16.0,
            "percent": 38.8
        },
        "disk": {
            "used": 892.1,
            "total": 1863.2,
            "percent": 47.9
        }
    }

# Honeypot admin panel (only accessible locally)
@app.get("/honeypot/admin")
async def honeypot_admin(request: Request):
    """Admin panel to view captured attacks"""
    # Only allow local access
    if request.client.host not in ["127.0.0.1", "localhost"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    return templates.TemplateResponse("admin_panel.html", {"request": request})

@app.get("/honeypot/api/attacks")
async def get_attack_data(request: Request):
    """API to get attack data for admin panel"""
    if request.client.host not in ["127.0.0.1", "localhost"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    db_path = HONEYPOT_DIR / "database" / "honeypot.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get recent login attempts
    cursor.execute("""
        SELECT timestamp, ip_address, username, password, user_agent, session_id
        FROM login_attempts 
        ORDER BY timestamp DESC 
        LIMIT 50
    """)
    login_attempts = [dict(zip([col[0] for col in cursor.description], row)) 
                     for row in cursor.fetchall()]
    
    # Get session summary
    cursor.execute("""
        SELECT session_id, ip_address, start_time, last_activity, 
               total_requests, attack_type, risk_level
        FROM attack_sessions 
        ORDER BY last_activity DESC 
        LIMIT 20
    """)
    sessions = [dict(zip([col[0] for col in cursor.description], row)) 
               for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "login_attempts": login_attempts,
        "sessions": sessions,
        "stats": {
            "total_attempts": len(login_attempts),
            "unique_attackers": len(set(attempt["ip_address"] for attempt in login_attempts)),
            "active_sessions": len([s for s in sessions if s["total_requests"] > 1])
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🍯 Starting MCP Honeypot on port 8001...")
    print("🚨 Admin panel: http://localhost:8001/honeypot/admin")
    uvicorn.run(app, host="0.0.0.0", port=8001)
