from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
import mimetypes
import psutil
import subprocess
import shutil
import aiofiles
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from utils import get_directory_structure, get_file_list, get_folder_contents, generate_thumbnail  # defined in utils.py

app = FastAPI()

BASE_PATH = Path("/media/mint/shared")  # NTFS shared partition

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Authentication Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

# Simple session storage (in production, use Redis or database)
active_sessions = {}

class SessionManager:
    @staticmethod
    def create_session(username: str) -> str:
        session_token = secrets.token_hex(32)
        active_sessions[session_token] = {
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        return session_token
    
    @staticmethod
    def validate_session(session_token: str) -> Optional[dict]:
        if session_token in active_sessions:
            session = active_sessions[session_token]
            # Check if session is still valid (24 hours)
            if datetime.now() - session["created_at"] < timedelta(hours=24):
                # Update last activity
                session["last_activity"] = datetime.now()
                return session
            else:
                # Session expired, remove it
                del active_sessions[session_token]
        return None
    
    @staticmethod
    def remove_session(session_token: str):
        if session_token in active_sessions:
            del active_sessions[session_token]

def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from cookies"""
    return request.cookies.get("session_token")

class AuthenticationRequired(Exception):
    pass

def require_auth(request: Request) -> dict:
    """Dependency to require authentication"""
    session_token = get_session_token(request)
    if not session_token:
        raise AuthenticationRequired()
    
    session = SessionManager.validate_session(session_token)
    if not session:
        raise AuthenticationRequired()
    
    return session

@app.exception_handler(AuthenticationRequired)
async def auth_exception_handler(request: Request, exc: AuthenticationRequired):
    """Redirect unauthenticated users to login"""
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Display login page"""
    # Check if already logged in
    session_token = get_session_token(request)
    if session_token and SessionManager.validate_session(session_token):
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Create session
        session_token = SessionManager.create_session(username)
        
        # Redirect to dashboard with session cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token", 
            value=session_token,
            max_age=86400,  # 24 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
    else:
        # Invalid credentials, redirect back to login with error
        return RedirectResponse(url="/login?error=Invalid username or password", status_code=302)

@app.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    session_token = get_session_token(request)
    if session_token:
        SessionManager.remove_session(session_token)
    
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    return response

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, path: str = "", session: dict = Depends(require_auth)):
    """Main dashboard - requires authentication"""
    current_path = (BASE_PATH / path).resolve()
    if not current_path.exists() or not current_path.is_dir():
        return HTMLResponse(content="Invalid path", status_code=404)

    directory_tree = get_directory_structure(BASE_PATH)
    files = get_file_list(current_path)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "directory_tree": directory_tree,
        "files": files,
        "current_path": str(current_path.relative_to(BASE_PATH)),
        "username": session["username"]
    })


@app.get("/file/{file_path:path}")
async def serve_file(file_path: str, request: Request, session: dict = Depends(require_auth)):
    full_path = (BASE_PATH / file_path).resolve()
    if not full_path.exists():
        return HTMLResponse("File not found", status_code=404)

    mime_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(str(full_path), media_type=mime_type or 'application/octet-stream')


# === API ENDPOINTS ===

@app.get("/api/diagnostics")
async def get_system_diagnostics(session: dict = Depends(require_auth)):
    """Get real-time system diagnostics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(BASE_PATH))
        
        return {
            "cpu": {
                "usage": round(cpu_percent, 1)
            },
            "memory": {
                "used": round(memory.used / (1024**3), 2),
                "total": round(memory.total / (1024**3), 2),
                "percent": round(memory.percent, 1)
            },
            "disk": {
                "used": round(disk.used / (1024**3), 2),
                "total": round(disk.total / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 1)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting diagnostics: {str(e)}")


@app.post("/api/restart-samba")
async def restart_samba_service():
    """Restart the Samba service"""
    try:
        # Check if running as root or if user has sudo access
        result = subprocess.run(
            ["sudo", "-n", "systemctl", "restart", "smbd"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {"status": "success", "message": "Samba service restarted successfully"}
        else:
            return {"status": "error", "message": f"Failed to restart Samba: {result.stderr}"}
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Restart command timed out"}
    except Exception as e:
        return {"status": "error", "message": f"Error restarting Samba: {str(e)}"}


@app.get("/api/thumbnail/{file_path:path}")
async def get_thumbnail(file_path: str):
    """Get or generate thumbnail for media files"""
    try:
        full_path = (BASE_PATH / file_path).resolve()
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        thumbnail_path = generate_thumbnail(full_path)
        if thumbnail_path and thumbnail_path.exists():
            return FileResponse(str(thumbnail_path))
        else:
            # Return original file if thumbnail generation fails
            return FileResponse(str(full_path))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating thumbnail: {str(e)}")


@app.get("/api/models")
async def get_models():
    """Get available system models/services (placeholder for future expansion)"""
    return {
        "models": [
            "System Monitor",
            "File Explorer", 
            "Samba Service",
            "Thumbnail Generator"
        ]
    }


@app.get("/favicon.ico")
async def get_favicon():
    """Return a simple favicon to prevent 404 errors"""
    # Return a simple response or you could serve an actual favicon file
    return FileResponse("static/favicon.ico") if Path("static/favicon.ico").exists() else HTMLResponse(status_code=204)


@app.get("/api/folder-contents")
async def get_folder_contents_api(folder_path: str = "", session: dict = Depends(require_auth)):
    """Get contents of a specific folder for the right panel"""
    try:
        if folder_path:
            current_path = (BASE_PATH / folder_path).resolve()
        else:
            current_path = BASE_PATH
            
        if not current_path.exists() or not current_path.is_dir():
            raise HTTPException(status_code=404, detail="Folder not found")
        
        if not str(current_path).startswith(str(BASE_PATH)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        contents = get_folder_contents(current_path, BASE_PATH)
        return contents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading folder: {str(e)}")


@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    """Download any file with proper headers"""
    try:
        full_path = (BASE_PATH / file_path).resolve()
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not str(full_path).startswith(str(BASE_PATH)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        
        return FileResponse(
            str(full_path), 
            media_type=mime_type or 'application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename=\"{full_path.name}\""}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), folder_path: str = Form(""), session: dict = Depends(require_auth)):
    """Upload a file to the specified folder"""
    try:
        # Determine target directory
        if folder_path:
            target_dir = (BASE_PATH / folder_path).resolve()
        else:
            target_dir = BASE_PATH
            
        # Security check - ensure we're not going outside BASE_PATH
        if not str(target_dir).startswith(str(BASE_PATH)):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct file path
        file_path = target_dir / file.filename
        
        # Check if file already exists
        if file_path.exists():
            # Add timestamp to make it unique
            import time
            timestamp = int(time.time())
            name, ext = file.filename.rsplit('.', 1) if '.' in file.filename else (file.filename, '')
            new_filename = f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"
            file_path = target_dir / new_filename
        
        # Save the file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "status": "success", 
            "message": f"File '{file.filename}' uploaded successfully",
            "file_path": str(file_path.relative_to(BASE_PATH))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/api/create-folder")
async def create_folder(folder_name: str = Form(...), parent_path: str = Form("")):
    """Create a new folder"""
    try:
        # Determine parent directory
        if parent_path:
            parent_dir = (BASE_PATH / parent_path).resolve()
        else:
            parent_dir = BASE_PATH
            
        # Security check
        if not str(parent_dir).startswith(str(BASE_PATH)):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Create new folder
        new_folder = parent_dir / folder_name
        new_folder.mkdir(parents=True, exist_ok=True)
        
        return {
            "status": "success", 
            "message": f"Folder '{folder_name}' created successfully",
            "folder_path": str(new_folder.relative_to(BASE_PATH))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

