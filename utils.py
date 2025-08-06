from pathlib import Path
import hashlib
import cv2
import os
from PIL import Image

def get_directory_structure(base_path: Path):
    """Get only root-level directories for the left sidebar"""
    structure = []
    
    try:
        for item in sorted(base_path.iterdir()):
            if item.is_dir():
                rel_path = str(item.relative_to(base_path))
                structure.append({
                    "name": item.name,
                    "path": rel_path,
                    "type": "folder"
                })
    except (PermissionError, FileNotFoundError):
        # Handle cases where we can't access the directory
        pass
    
    return structure


def get_folder_contents(folder_path: Path, base_path: Path):
    """Get contents of a specific folder (both subfolders and files)"""
    contents = {"folders": [], "files": []}
    
    try:
        for item in sorted(folder_path.iterdir()):
            if item.is_dir():
                rel_path = str(item.relative_to(base_path))
                contents["folders"].append({
                    "name": item.name,
                    "path": rel_path,
                    "type": "folder"
                })
            elif item.is_file():
                # Reuse the existing file categorization logic
                file_info = categorize_file(item, base_path)
                contents["files"].append(file_info)
    except (PermissionError, FileNotFoundError):
        pass
    
    return contents


def categorize_file(file_path: Path, base_path: Path):
    """Categorize a file by type and return file info"""
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
    video_exts = [".mp4", ".webm", ".ogg", ".avi", ".mov", ".mkv", ".flv"]
    
    ext = file_path.suffix.lower()
    file_type = "other"
    
    if ext in image_exts:
        file_type = "image"
    elif ext in video_exts:
        file_type = "video"
    
    return {
        "name": file_path.name,
        "path": str(file_path.relative_to(base_path)),
        "type": file_type,
        "size": file_path.stat().st_size if file_path.exists() else 0
    }


def get_file_list(path: Path):
    """Legacy function for compatibility - returns files in current directory"""
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    video_exts = [".mp4", ".webm", ".ogg"]
    files = []

    for item in path.iterdir():
        if item.is_file():
            ext = item.suffix.lower()
            file_type = None
            if ext in image_exts:
                file_type = "image"
            elif ext in video_exts:
                file_type = "video"
            else:
                file_type = "other"

            files.append({
                "name": item.name,
                "path": str(item.relative_to(path.parent)),
                "type": file_type
            })

    return files


def generate_thumbnail(file_path: Path, thumbnail_dir: Path = Path("thumbnails"), size: tuple = (200, 200)):
    """Generate thumbnail for image or video files"""
    try:
        # Create thumbnail directory if it doesn't exist
        thumbnail_dir.mkdir(exist_ok=True)
        
        # Create a unique filename based on the original file path
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        thumbnail_path = thumbnail_dir / f"{file_hash}.jpg"
        
        # Return existing thumbnail if it exists and is newer than source
        if thumbnail_path.exists() and thumbnail_path.stat().st_mtime > file_path.stat().st_mtime:
            return thumbnail_path
        
        file_ext = file_path.suffix.lower()
        
        # Handle image files
        if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]:
            try:
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    # Create thumbnail
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    img.save(thumbnail_path, "JPEG", quality=85, optimize=True)
                    return thumbnail_path
            except Exception as e:
                print(f"Error creating image thumbnail for {file_path}: {e}")
                return None
        
        # Handle video files
        elif file_ext in [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]:
            try:
                cap = cv2.VideoCapture(str(file_path))
                
                # Try to seek to 10% of video length for a better frame
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if frame_count > 10:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 10)
                
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Create PIL image and thumbnail
                    img = Image.fromarray(frame)
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    img.save(thumbnail_path, "JPEG", quality=85, optimize=True)
                    return thumbnail_path
                else:
                    print(f"Could not read frame from video: {file_path}")
                    return None
            except Exception as e:
                print(f"Error creating video thumbnail for {file_path}: {e}")
                return None
        
        # Unsupported file type
        return None
        
    except Exception as e:
        print(f"Error in thumbnail generation for {file_path}: {e}")
        return None