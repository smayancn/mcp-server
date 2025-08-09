# 🍯 MCP Honeypot - Phase 1

## Overview
A cybersecurity honeypot that mimics my real MCP file server to capture and analyze attacker behavior.

## Architecture
```
Port 8000: Real MCP File Server (my actual files)
Port 8001: Honeypot (fake login that captures attacks)
```

## Features Implemented ✅

### 🎯 **Honeypot Core**
- **Fake Login Page**: Identical to real MCP interface
- **Attack Logging**: SQLite database + JSON logs
- **Session Tracking**: Links multiple requests from same attacker
- **Behavioral Capture**: Logs all interactions, credentials, user agents

### 📊 **Admin Dashboard** 
- **Real-time Monitoring**: Live attack statistics
- **Attack Analysis**: View login attempts, session data
- **Security Dashboard**: Professional-grade admin interface
- **Auto-refresh**: Updates every 30 seconds

### 🔒 **Security Features**
- **Admin Panel Protection**: Localhost-only access
- **Data Logging**: Multiple formats (DB + JSON)
- **Session Fingerprinting**: Track attackers across interactions

## Quick Start

### 1. Start Real File Server
```bash
cd /home/mint/Desktop/mcp-server
python3 start.py
# Runs on http://localhost:8000
```

### 2. Start the Honeypot
```bash
cd /home/mint/Desktop/mcp-server/honeypot
python3 start_honeypot.py
# Runs on http://localhost:8001
```

### 3. Access Admin Panel
```
http://localhost:8001/honeypot/admin
```

## How It Works

### For Attackers (Port 8001):
1. **Login Page**: Looks exactly like your real MCP
2. **Credential Capture**: Logs all username/password attempts
3. **Fake Dashboard**: Shows believable but fake file system
4. **Behavioral Logging**: Records all clicks, interactions

### For You (Localhost Only):
1. **Admin Dashboard**: View all captured attacks
2. **Real File Server**: Access your actual files on port 8000
3. **Attack Analytics**: Understand attacker patterns

## Data Collected

### 🔍 **Attack Intelligence**
- IP addresses and geolocations
- Login credentials attempted
- User agent strings (tools used)
- Session duration and patterns
- File access attempts
- Command injection attempts

### 📈 **Analytics**
- Attack frequency patterns
- Most common credentials
- Attacker skill level indicators
- Tool signatures (automated vs manual)

## File Structure
```
honeypot/
├── honeypot_main.py      # Main FastAPI application
├── start_honeypot.py     # Startup script
├── templates/            # HTML templates
│   ├── fake_login.html   # Fake login page
│   ├── fake_dashboard.html # Fake file browser
│   └── admin_panel.html  # Security dashboard
├── database/             # SQLite attack database
├── logs/                 # JSON log files
└── static/              # CSS/JS assets
```

## Next Phase: AI Agent 

### Coming Next:
- **Threat Classification**: AI analysis of attack patterns
- **Risk Assessment**: Automated threat scoring
- **Attack Prediction**: Anticipate next steps
- **Security Recommendations**: AI-generated defense suggestions
- **Real-time Alerts**: Notify of sophisticated attacks

## Security Notes ⚠️

1. **Admin Panel**: Only accessible from localhost
2. **Data Privacy**: All logs stored locally
3. **Network Isolation**: Honeypot can't access real files
4. **Monitoring**: Check logs regularly for real threats

## Resume Value 🎖️

This demonstrates:
- **Cybersecurity Engineering**: Honeypot design and implementation
- **Threat Intelligence**: Attack data collection and analysis  
- **Python Development**: FastAPI, SQLite, async programming
- **Security Analytics**: Real-time monitoring and reporting
- **Incident Response**: Automated threat detection

---

**Phase 1 Complete!** ✅ 
Ready for AI agent integration in Phase 2.
