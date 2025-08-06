// Modern MCP Dashboard JavaScript
document.addEventListener("DOMContentLoaded", () => {
    // Initialize the dashboard
    initializeDashboard();
});

function initializeDashboard() {
    // Update system stats on load
    updateSystemStats();
    
    // Set up event listeners
    setupEventListeners();
    
    // Update stats every 30 seconds
    setInterval(updateSystemStats, 30000);
}

function setupEventListeners() {
    // Restart Samba button
    const restartSambaBtn = document.getElementById("restart-samba");
    if (restartSambaBtn) {
        restartSambaBtn.addEventListener("click", handleRestartSamba);
    }
    
    // Refresh stats button
    const refreshStatsBtn = document.getElementById("refresh-stats");
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener("click", updateSystemStats);
    }
}

// Update system statistics in the header
async function updateSystemStats() {
    try {
        const response = await fetch("/api/diagnostics");
        if (response.ok) {
            const data = await response.json();
            
            // Update CPU stat
            const cpuStat = document.getElementById("cpu-stat");
            if (cpuStat) {
                cpuStat.textContent = `CPU: ${data.cpu.usage}%`;
            }
            
            // Update Memory stat
            const memoryStat = document.getElementById("memory-stat");
            if (memoryStat) {
                memoryStat.textContent = `RAM: ${data.memory.used}/${data.memory.total} GB (${data.memory.percent}%)`;
            }
            
            // Update Disk stat
            const diskStat = document.getElementById("disk-stat");
            if (diskStat) {
                diskStat.textContent = `Disk: ${data.disk.used}/${data.disk.total} GB (${data.disk.percent}%)`;
            }
        } else {
            console.error("Failed to fetch diagnostics");
            updateStatsError();
        }
    } catch (error) {
        console.error("Error fetching system stats:", error);
        updateStatsError();
    }
}

function updateStatsError() {
    ["cpu-stat", "memory-stat", "disk-stat"].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = element.textContent.split(":")[0] + ": Error";
        }
    });
}

// Handle Samba service restart
async function handleRestartSamba() {
    const button = document.getElementById("restart-samba");
    const originalText = button.textContent;
    
    try {
        // Update button state
        button.disabled = true;
        button.textContent = "🔄 Restarting...";
        
        const response = await fetch("/api/restart-samba", { method: "POST" });
        const data = await response.json();
        
        if (data.status === "success") {
            showNotification("✅ Samba service restarted successfully!", "success");
        } else {
            showNotification(`❌ Failed to restart Samba: ${data.message}`, "error");
        }
    } catch (error) {
        console.error("Error restarting Samba:", error);
        showNotification("❌ Error restarting Samba service", "error");
    } finally {
        // Restore button state
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Global variable to track current path
let currentFolderPath = "";

// Load folder contents when clicking on left sidebar folders
async function loadFolderContents(folderPath, buttonElement) {
    try {
        // Update active state
        document.querySelectorAll('.folder-btn').forEach(btn => btn.classList.remove('active'));
        buttonElement.classList.add('active');
        
        // Show loading
        const loading = document.getElementById('loading');
        const folderContents = document.getElementById('folder-contents');
        const breadcrumb = document.querySelector('.breadcrumb');
        
        loading.style.display = 'flex';
        folderContents.style.display = 'none';
        
        // Update breadcrumb
        breadcrumb.textContent = `📍 Current Path: /media/nas/${folderPath}`;
        
        // Store current path
        currentFolderPath = folderPath;
        
        // Fetch folder contents
        const response = await fetch(`/api/folder-contents?folder_path=${encodeURIComponent(folderPath)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide loading
        loading.style.display = 'none';
        folderContents.style.display = 'block';
        
        // Render contents
        renderFolderContents(data);
        
    } catch (error) {
        console.error('Error loading folder contents:', error);
        showNotification(`❌ Error loading folder: ${error.message}`, 'error');
        
        // Hide loading and show error
        document.getElementById('loading').style.display = 'none';
        document.getElementById('folder-contents').innerHTML = `
            <div class="empty-state">
                <div class="icon">⚠️</div>
                <p>Error loading folder contents</p>
            </div>
        `;
        document.getElementById('folder-contents').style.display = 'block';
    }
}

// Render folder contents in the right panel
function renderFolderContents(data) {
    const container = document.getElementById('folder-contents');
    let html = '';
    
    // Show folders first
    if (data.folders && data.folders.length > 0) {
        html += '<h3 class="section-header">📁 Folders</h3>';
        html += '<div class="mixed-grid">';
        data.folders.forEach(folder => {
            html += `
                <div class="folder-item" onclick="navigateToFolder('${folder.path}')">
                    <div class="folder-icon">📁</div>
                    <div class="filename">${folder.name}</div>
                    <button class="download-btn" onclick="event.stopPropagation(); downloadFolder('${folder.path}')">
                        📦 Browse
                    </button>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Show files
    if (data.files && data.files.length > 0) {
        html += '<h3 class="section-header">📄 Files</h3>';
        html += '<div class="mixed-grid">';
        data.files.forEach(file => {
            const fileSize = formatFileSize(file.size);
            html += `
                <div class="file-item">
                    <div class="media-container" onclick="handleFileClick('${file.path}', '${file.type}')">
                        ${renderFilePreview(file)}
                    </div>
                    <div class="filename">${file.name}</div>
                    <div style="font-size: 12px; color: #5f6368; margin-bottom: 8px;">${fileSize}</div>
                    <button class="download-btn" onclick="downloadFile('${file.path}')">
                        ⬇️ Download
                    </button>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Show empty state if no content
    if ((!data.folders || data.folders.length === 0) && (!data.files || data.files.length === 0)) {
        html = `
            <div class="empty-state">
                <div class="icon">📂</div>
                <p>This folder is empty</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Navigate to a subfolder
function navigateToFolder(folderPath) {
    // Find the corresponding folder button or create a temporary one
    const folderName = folderPath.split('/').pop();
    loadFolderContents(folderPath, { classList: { add: () => {}, remove: () => {} } });
}

// Render file preview based on type
function renderFilePreview(file) {
    if (file.type === "image") {
        return `<img src="/file/${file.path}" alt="${file.name}" loading="lazy" />`;
    } else if (file.type === "video") {
        return `<video src="/file/${file.path}" muted preload="metadata"></video>`;
    } else {
        let icon = "📄";
        if (file.name.endsWith('.pdf')) icon = "📄";
        else if (file.name.endsWith('.txt') || file.name.endsWith('.md')) icon = "📝";
        else if (file.name.endsWith('.zip') || file.name.endsWith('.rar')) icon = "📦";
        else if (file.name.endsWith('.mp3') || file.name.endsWith('.wav')) icon = "🎵";
        
        return `<div class="file-icon">${icon}</div>`;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Download file
function downloadFile(filePath) {
    window.open(`/api/download/${filePath}`, '_blank');
}

// Download/browse folder
function downloadFolder(folderPath) {
    // Navigate to the folder
    navigateToFolder(folderPath);
}

// File click handler
function handleFileClick(filePath, fileType) {
    if (fileType === "image") {
        openImageModal(filePath);
    } else if (fileType === "video") {
        openVideoModal(filePath);
    } else {
        // For other files, download them
        downloadFile(filePath);
    }
}

// Open image in modal
function openImageModal(filePath) {
    const modal = createModal();
    modal.innerHTML = `
        <div class="modal-content image-modal">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <img src="/file/${filePath}" alt="Image preview" style="max-width: 90vw; max-height: 90vh; object-fit: contain;">
        </div>
    `;
    document.body.appendChild(modal);
}

// Open video in modal
function openVideoModal(filePath) {
    const modal = createModal();
    modal.innerHTML = `
        <div class="modal-content video-modal">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <video controls style="max-width: 90vw; max-height: 90vh;">
                <source src="/file/${filePath}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
    `;
    document.body.appendChild(modal);
}

// Create modal element
function createModal() {
    const modal = document.createElement("div");
    modal.className = "modal";
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    // Close modal on background click
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });
    
    return modal;
}

// Close modal
function closeModal() {
    const modal = document.querySelector(".modal");
    if (modal) {
        modal.remove();
    }
}

// Show notification
function showNotification(message, type = "info") {
    // Remove existing notifications
    const existing = document.querySelector(".notification");
    if (existing) existing.remove();
    
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        background: ${type === "success" ? "#4caf50" : type === "error" ? "#f44336" : "#2196f3"};
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

// Modal styles (add to CSS)
const modalStyles = `
    .modal-content {
        position: relative;
        background: white;
        border-radius: 8px;
        max-width: 95vw;
        max-height: 95vh;
        overflow: hidden;
    }
    
    .modal-close {
        position: absolute;
        top: 10px;
        right: 15px;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        border: none;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        z-index: 1002;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-close:hover {
        background: rgba(0, 0, 0, 0.9);
    }
`;

// Add modal styles to head
if (!document.querySelector("#modal-styles")) {
    const style = document.createElement("style");
    style.id = "modal-styles";
    style.textContent = modalStyles;
    document.head.appendChild(style);
}

