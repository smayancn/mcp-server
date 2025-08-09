from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import mimetypes
import psutil
import subprocess
import shutil
import aiofiles
from utils import get_directory_structure, get_file_list, get_folder_contents, generate_thumbnail  # defined in utils.py

app = FastAPI()

BASE_PATH = Path("/media/mint/shared")  # NTFS shared partition

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, path: str = ""):
    current_path = (BASE_PATH / path).resolve()
    if not current_path.exists() or not current_path.is_dir():
        return HTMLResponse(content="Invalid path", status_code=404)

    directory_tree = get_directory_structure(BASE_PATH)
    files = get_file_list(current_path)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "directory_tree": directory_tree,
        "files": files,
        "current_path": str(current_path.relative_to(BASE_PATH))
    })


@app.get("/file/{file_path:path}")
async def serve_file(file_path: str):
    full_path = (BASE_PATH / file_path).resolve()
    if not full_path.exists():
        return HTMLResponse("File not found", status_code=404)

    mime_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(str(full_path), media_type=mime_type or 'application/octet-stream')


# === API ENDPOINTS ===

@app.get("/api/diagnostics")
async def get_system_diagnostics():
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
async def get_folder_contents_api(folder_path: str = ""):
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
async def upload_file(file: UploadFile = File(...), folder_path: str = Form("")):
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

