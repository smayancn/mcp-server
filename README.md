# MCP Server - Media Center Platform

A fast, aesthetic, Google Drive-style web dashboard for managing local media, monitoring system diagnostics, and controlling server services — built using FastAPI and vanilla JavaScript.

![MCP Server Dashboard](https://img.shields.io/badge/FastAPI-0.116.1-green) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 📁 Interactive File Explorer
- **Smart Left Panel**: Shows only root folders from `/media/nas`
- **Dynamic Right Panel**: Displays folder contents (subfolders + files) when clicking left panel folders
- **Responsive Grid View**: Beautiful rectangular grid layout with thumbnails for images/videos
- **Breadcrumb Navigation**: Real-time path updates as you navigate
- **File Type Detection**: Smart icons for different file types (images, videos, documents, etc.)

### 💻 System Diagnostics
- **Real-time Monitoring**: Live CPU, memory, and disk usage stats in header
- **Auto-refresh**: Stats update every 30 seconds automatically
- **RESTful API**: `/api/diagnostics` endpoint for system information

### 🔄 Service Controls
- **One-click Samba Restart**: Restart Samba service with a single button click
- **Interactive Feedback**: Loading states and success/error notifications
- **Secure Operations**: Proper sudo access checks and timeout protection

### 🖼️ Advanced Thumbnails
- **Auto-generated**: Thumbnails for images and videos (200x200px)
- **Smart Caching**: Hash-based filename caching system
- **Performance Optimized**: Only regenerates when source file is newer
- **Format Support**: JPG, PNG, GIF, WebP, MP4, AVI, MOV, MKV, etc.

### ⬇️ Universal Downloads
- **Everything Downloadable**: Download buttons on all files
- **Secure Downloads**: Proper security checks and MIME type detection
- **Direct File Access**: `/file/{path}` endpoint for direct media serving
- **Download API**: `/api/download/{path}` with proper headers

### 🎨 Modern UI/UX
- **Google Drive Inspired**: Clean, professional design with modern aesthetics
- **Modal Viewers**: Full-screen image and video viewing
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Toast Notifications**: User feedback for all actions
- **Loading States**: Smooth loading indicators during operations

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Access to `/media/nas` directory (or configure custom path)
- Sudo access for Samba service control (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. **Set up virtual environment**
   ```bash
   cd mcp-drive
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn psutil opencv-python-headless pillow "numpy<2"
   ```

4. **Configure media path** (optional)
   
   Edit `main.py` line 14 to change the base media directory:
   ```python
   BASE_PATH = Path("/your/media/path")  # Change this to your media location
   ```

5. **Run the server**
   ```bash
   # Option 1: Use the launcher (auto-opens browser)
   python start.py
   
   # Option 2: Manual start
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the dashboard**
   
   Open your browser and navigate to: **http://localhost:8000**

## 📁 Project Structure

```
mcp-server/
├── mcp-drive/                    # Main application directory
│   ├── main.py                   # FastAPI server and API endpoints
│   ├── utils.py                  # Directory utilities and thumbnail generation
│   ├── models.py                 # Pydantic models for data validation
│   ├── start.py                  # Application launcher (auto-opens browser)
│   ├── requirements.txt          # Python dependencies
│   ├── static/                   # Frontend assets
│   │   ├── app.js               # JavaScript for UI interactivity
│   │   ├── style.css            # Google Drive-style CSS
│   │   └── icons/               # File type icons
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── dashboard.html       # Main UI template
│   │   └── ...
│   ├── thumbnails/              # Auto-generated thumbnails
│   ├── cache/                   # Application cache
│   ├── logs/                    # Application logs
│   └── venv/                    # Python virtual environment
└── README.md                    # This file
```

## 🔧 Configuration

### Media Path Configuration
The default media path is set to `/media/nas`. To change this:

1. Edit `main.py`:
   ```python
   BASE_PATH = Path("/your/custom/path")
   ```

2. Ensure the path exists and has proper read permissions

### Thumbnail Settings
Thumbnail generation can be customized in `utils.py`:

```python
def generate_thumbnail(file_path: Path, thumbnail_dir: Path = Path("thumbnails"), size: tuple = (200, 200)):
```

### Server Configuration
Modify the server settings in the startup commands:

```bash
# Change host and port
uvicorn main:app --host 0.0.0.0 --port 8080

# Enable debug mode
uvicorn main:app --reload --log-level debug
```

## 📚 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main dashboard interface |
| `GET` | `/file/{file_path}` | Direct file serving |
| `GET` | `/api/diagnostics` | System stats (CPU, RAM, disk) |
| `POST` | `/api/restart-samba` | Restart Samba service |
| `GET` | `/api/folder-contents` | Get folder contents |
| `GET` | `/api/download/{file_path}` | Download files with headers |
| `GET` | `/api/thumbnail/{file_path}` | Get/generate thumbnails |
| `GET` | `/api/models` | Available system services |

### Example API Responses

**System Diagnostics** (`/api/diagnostics`):
```json
{
  "cpu": {"usage": 25.3},
  "memory": {
    "used": 8.45,
    "total": 16.0,
    "percent": 52.8
  },
  "disk": {
    "used": 245.7,
    "total": 500.0,
    "percent": 49.1
  }
}
```

**Folder Contents** (`/api/folder-contents?folder_path=photos`):
```json
{
  "folders": [
    {
      "name": "vacation",
      "path": "photos/vacation",
      "type": "folder"
    }
  ],
  "files": [
    {
      "name": "sunset.jpg",
      "path": "photos/sunset.jpg",
      "type": "image",
      "size": 2547392
    }
  ]
}
```

## 🛠️ Development

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Update `static/app.js` for new functionality
3. **Styling**: Modify `static/style.css` for UI changes
4. **Templates**: Edit HTML templates in `templates/`

### Debugging

Enable debug mode for development:
```bash
uvicorn main:app --reload --log-level debug
```

### Testing

Test API endpoints using curl:
```bash
# Test system diagnostics
curl http://localhost:8000/api/diagnostics

# Test folder contents
curl "http://localhost:8000/api/folder-contents?folder_path=photos"
```

## 🔒 Security Features

- **Path Traversal Protection**: Prevents access outside the configured media directory
- **File Access Validation**: Ensures files exist and are accessible before serving
- **Sudo Access Control**: Secure service restart with timeout protection
- **MIME Type Detection**: Proper content type headers for all file types
- **Error Handling**: Comprehensive error responses for invalid requests

## 🎯 Use Cases

- **Home Media Server**: Browse and stream personal media collections
- **NAS Management**: Visual interface for network-attached storage
- **Server Monitoring**: Keep track of system performance
- **File Sharing**: Easy download access for family/team members
- **Media Organization**: Visual browsing of large media libraries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Server won't start**
- Check if port 8000 is available
- Ensure all dependencies are installed
- Verify Python 3.10+ is being used

**Thumbnails not generating**
- Install OpenCV: `pip install opencv-python-headless`
- Check file permissions in thumbnails directory
- Verify media files are not corrupted

**Samba restart fails**
- Ensure user has sudo privileges
- Check if Samba service exists: `systemctl status smbd`
- Verify sudo access without password prompt

**Files not accessible**
- Check media directory permissions
- Ensure BASE_PATH is correctly configured
- Verify files exist and are readable

### Getting Help

If you encounter issues:
1. Check the logs in the `logs/` directory
2. Enable debug mode for detailed error messages
3. Verify all dependencies are correctly installed
4. Check file and directory permissions

## 🌟 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Styled with Google Drive-inspired design principles
- Uses [OpenCV](https://opencv.org/) for video thumbnail generation
- Powered by [Pillow](https://pillow.readthedocs.io/) for image processing

---

**Made with ❤️ for modern media management**
