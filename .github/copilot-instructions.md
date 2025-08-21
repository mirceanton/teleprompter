# Remote Teleprompter

Remote Teleprompter is a Python FastAPI web application that enables real-time teleprompter control between devices. One device (computer) acts as a controller to edit scripts and manage playback, while another device (phone/tablet) displays the teleprompter text. Communication happens via WebSockets for real-time synchronization.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Run the Application
- **Install Python dependencies**: `pip install -r requirements.txt` -- takes 30 seconds. NEVER CANCEL.
- **Start the application**: `python3 main.py` -- starts in 2-3 seconds on http://0.0.0.0:8000
- **Health check**: `curl http://localhost:8000/health` -- returns {"status":"healthy","active_channels":0}
- **Stop the application**: Use Ctrl+C in the terminal running main.py

### Docker (Known Limitation)
- **Docker build fails** in sandbox environments due to SSL certificate issues when installing Python packages
- `docker build .` will fail with SSL certificate verification errors
- Use direct Python execution instead: `python3 main.py`

## Validation

### CRITICAL: Manual Functional Testing Required
After making any changes, ALWAYS run through this complete validation scenario:

1. **Start the application**: `python3 main.py`
2. **Open browser**: Navigate to http://localhost:8000
3. **Test Controller Mode**:
   - Click "💻 Controller Mode" button
   - Enter any channel name (e.g., "test-channel")
   - Click "Connect to Channel"
   - Verify status shows "Connected - CONTROLLER Mode"
   - Verify script editor appears with default text
   - Test controls: click "▶️ Start", "⏸️ Pause", "⏮️ Reset" buttons
   - Modify text in script editor and click "🔄 Sync Text"
   - Adjust speed slider and text width slider
4. **Test Teleprompter Mode** (optional, in new browser tab):
   - Open new tab to http://localhost:8000
   - Click "📱 Teleprompter Mode" button
   - Use same channel name as controller
   - Click "Connect to Channel"
   - Verify teleprompter display appears
5. **Verify WebSocket Communication**:
   - Check terminal output for WebSocket connection messages
   - Look for messages like "Client connected to channel: [channel-name]"
   - Verify control commands generate "Received [command] message" logs

### No Automated Tests
- **No test framework** is configured in this repository
- **No linting tools** are configured
- Manual functional testing is the primary validation method
- Always test the complete user workflow above after making changes

## Common Tasks

### Repository Structure
```
/home/runner/work/teleprompter/teleprompter/
├── main.py                    # FastAPI backend with WebSocket handling
├── requirements.txt           # Python dependencies (FastAPI, uvicorn, websockets)
├── templates/
│   └── index.html            # Main UI template with controller/teleprompter modes
├── static/
│   ├── css/
│   │   └── style.css         # Application styling
│   └── js/
│       └── app.js           # Frontend JavaScript with WebSocket logic
├── Dockerfile               # Docker configuration (build fails in sandbox)
├── compose.yaml            # Docker Compose configuration
└── .github/
    └── workflows/
        ├── docker-build-push.yaml  # CI/CD for Docker images
        └── git-release.yaml         # Release automation
```

### Key Application Components
- **FastAPI Backend** (`main.py`): Serves HTML template, static files, WebSocket endpoints
- **WebSocket Communication**: Real-time messaging between controller and teleprompter modes
- **Frontend JavaScript** (`static/js/app.js`): Handles UI interactions, WebSocket connections, mode switching
- **HTML Template** (`templates/index.html`): Single-page application with both controller and teleprompter interfaces

### Making Changes
1. **Backend changes**: Edit `main.py` for API endpoints, WebSocket handling, or server configuration
2. **Frontend logic**: Edit `static/js/app.js` for UI behavior, WebSocket communication, or control logic  
3. **UI styling**: Edit `static/css/style.css` for visual appearance
4. **HTML structure**: Edit `templates/index.html` for layout or new UI elements
5. **Dependencies**: Edit `requirements.txt` for new Python packages

### Development Workflow
1. Make your changes to the relevant files
2. **ALWAYS restart the application** after backend changes: Stop with Ctrl+C, run `python3 main.py`
3. **Frontend changes** take effect immediately (refresh browser)
4. **Run complete functional validation** using the scenario above
5. Check terminal logs for any WebSocket connection issues or errors

### Debugging
- **WebSocket issues**: Check browser developer console for connection errors
- **Backend errors**: Monitor terminal output where `python3 main.py` is running
- **Connection problems**: Verify both devices use the same channel name
- **UI issues**: Use browser developer tools to inspect HTML/CSS/JavaScript

## Time Expectations
- **Dependency installation**: 30 seconds. NEVER CANCEL.
- **Application startup**: 2-3 seconds. NEVER CANCEL.
- **Functional testing**: 2-3 minutes for complete validation scenario
- **Docker build**: FAILS in sandbox environments - do not attempt

## Requirements
- **Python 3.11+** (tested with Python 3.12.3)
- **pip** for dependency management
- **Modern web browser** for functional testing
- **Network access** for installing Python packages (pip install)

## Known Limitations
- **Docker build fails** in sandboxed environments due to SSL certificate verification
- **No automated test suite** - rely on manual functional testing
- **No linting configuration** - manual code review required
- **Single-file backend** - all FastAPI logic in main.py