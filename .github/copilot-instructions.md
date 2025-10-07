# Remote Teleprompter

Remote Teleprompter is a multi-device teleprompter application with a FastAPI backend and Vue.js frontend. One device (computer) acts as a controller to edit scripts and manage playback, while one or more other devices (phones/tablets) display the teleprompter text. Communication happens via WebSockets for real-time synchronization between all connected clients.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Architecture Overview

This is a **split architecture** application:
- **Backend**: FastAPI (Python) running on port 8000 (dev) or 8001 (Docker)
- **Frontend**: Vue.js + Vite serving a static SPA on port 3000 (dev) or 8000 (Docker)
- **Communication**: WebSockets for real-time bidirectional messaging
- **State Management**: Redis (required) for multi-instance synchronization via pub/sub

## Working Effectively

### Development Workflow (Local - Hot Reloading)

For active development with hot-reloading capabilities, run services locally **without Docker**:

**Backend** (from `backend/` directory):
```bash
pip install -r requirements.txt
python3 src/main.py
```
- Runs on **http://0.0.0.0:8000**
- Auto-reloads on file changes (uvicorn watch)
- **Requires Redis running**: Start Redis with `docker run -d -p 6379:6379 redis:alpine` or use Docker Compose

**Frontend** (from `frontend/` directory):
```bash
npm install
npm run dev
```
- Runs on **http://localhost:3000**
- Hot module replacement (HMR) enabled
- Vite dev server with instant updates

**Important**: When developing locally, the frontend (`config.json`) should point to `http://localhost:8000` for the backend API.

### Docker Testing Workflow

Before pushing to git, **always test with Docker** to ensure production build works:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

This command:
- Builds both frontend and backend images locally
- Runs with Redis for multi-instance testing
- Maps ports: **frontend on 8000**, **backend on 8001**
- Validates production build process

### Production Deployment

For production deployments (uses pre-built images from GHCR):

```bash
docker compose up -d
```

This pulls and runs the latest production images with Redis included by default.

## Validation

### Manual Functional Testing

Manual testing is the primary validation method. After making changes, test the complete workflow:

**Using Docker Compose** (recommended before pushing):
1. Start services: `docker compose -f compose.yaml -f compose.dev.yaml up --build`
2. Access frontend at **http://localhost:8000**
3. Test all three pages:
   - **Landing Page**: Verify both mode buttons are visible
   - **Controller Mode**: Test script editing, playback controls (start/pause/reset), speed slider, text width
   - **Teleprompter Mode**: Verify text display and scrolling synchronization
4. Verify backend health at **http://localhost:8001/api/health**
5. Check terminal logs for WebSocket connections and Redis connectivity

**Using Local Development** (for quick iteration):
1. Start backend: `cd backend && python3 src/main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Access frontend at **http://localhost:3000**
4. Test the same three pages as above
5. Monitor terminal output in both backend and frontend terminals

### Key Testing Scenarios
- **Multi-device sync**: Open controller on one device, teleprompter on another with same channel name
- **WebSocket communication**: Verify real-time updates when changing speed, text, or playback state
- **Reconnection**: Test behavior when refreshing pages or losing connection

### No Automated Tests
- **No test framework** is configured in this repository
- **No linting tools** are configured (though code follows Python/JavaScript conventions)
- Manual functional testing is required for all changes

## Common Tasks

### Repository Structure
```
/home/mircea/Workspace/apps/teleprompter/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt           # Python dependencies
│   └── src/
│       ├── main.py               # FastAPI app, WebSocket endpoints, startup logic
│       ├── connection_manager.py # WebSocket connection management
│       └── redis_manager.py      # Redis pub/sub for multi-instance support
├── frontend/
│   ├── Dockerfile
│   ├── package.json              # Node.js dependencies
│   ├── vite.config.js            # Vite configuration
│   ├── nginx.conf                # NGINX config for production
│   ├── index.html                # HTML entry point
│   ├── public/
│   │   └── config.json          # Runtime config (backend URL)
│   └── src/
│       ├── main.js               # Vue app entry point
│       ├── App.vue               # Root Vue component
│       ├── utils/
│       │   └── config.js        # Config loader utility
│       └── views/
│           ├── Landing.vue       # Mode selection page
│           ├── Controller.vue    # Script editor and controls
│           └── Teleprompter.vue  # Text display page
├── .img/                         # Screenshots for README
├── compose.yaml                  # Production Docker Compose (pre-built images + Redis)
├── compose.dev.yaml              # Development override (local builds)
└── .github/
    ├── copilot-instructions.md
    └── workflows/
        ├── docker-build-push.yaml  # CI/CD for Docker images
        └── git-release.yaml         # Release automation
```

### Key Application Components

**Backend (FastAPI + Python)**:
- `main.py`: FastAPI application, WebSocket endpoints (`/ws/{channel}`), health check, startup/shutdown logic
- `connection_manager.py`: Manages WebSocket connections per channel, broadcasts messages
- `redis_manager.py`: Optional Redis pub/sub for synchronizing state across multiple backend replicas

**Frontend (Vue.js + Vite)**:
- `Landing.vue`: Initial page where users select Controller or Teleprompter mode
- `Controller.vue`: Script editor, playback controls (start/pause/reset), speed/width sliders
- `Teleprompter.vue`: Full-screen text display that scrolls based on controller commands
- `config.json`: Runtime configuration file (backend URL must be hostname/IP, not localhost)

**Communication**:
- WebSocket channels identified by user-provided channel names
- Messages: `join`, `text`, `start`, `pause`, `reset`, `speed`, `width`, `mode`
- Real-time bidirectional sync between all connected clients on same channel

### Making Changes

**Backend changes** (`backend/src/`):
1. Edit `main.py` for API endpoints, WebSocket logic, startup/shutdown handlers
2. Edit `connection_manager.py` for WebSocket connection handling and broadcasting
3. Edit `redis_manager.py` for Redis pub/sub functionality
4. Update `requirements.txt` for new Python packages
5. **Restart required**: Stop backend (Ctrl+C) and run `python3 src/main.py` again

**Frontend changes** (`frontend/src/`):
1. Edit Vue components in `views/` for UI changes (Landing, Controller, Teleprompter)
2. Edit `App.vue` for routing or global layout changes
3. Edit `utils/config.js` for configuration loading logic
4. Update `package.json` for new npm packages
5. **Auto-reload**: Changes apply immediately via Vite HMR (just save the file)

**Configuration changes**:
- Backend: Environment variables or defaults in `redis_manager.py`
- Frontend: `public/config.json` for runtime configuration (backend URL)
- Docker: `compose.yaml` (production) or `compose.dev.yaml` (development overrides)

### Development Workflow
1. Make changes to backend or frontend files
2. **Backend**: Restart with Ctrl+C then `python3 src/main.py` (from `backend/` dir)
3. **Frontend**: Changes auto-reload via Vite HMR (no restart needed)
4. Test changes in browser (refresh if needed)
5. **Before committing**: Test with Docker Compose to validate production build
6. Check terminal logs for errors or WebSocket connection issues

### Debugging
- **WebSocket issues**: Check browser developer console (Network tab → WS) for connection errors
- **Backend errors**: Monitor terminal where `python3 src/main.py` is running for stack traces
- **Frontend errors**: Check browser console for JavaScript errors
- **Connection problems**: Ensure both devices use the same channel name
- **Port conflicts**: Backend uses 8000 (dev) or 8001 (Docker), frontend uses 3000 (dev) or 8000 (Docker)
- **Redis errors**: Check if Redis is running (Docker only) or remove Redis dependency for single-instance deployments
- **Config issues**: Verify `frontend/public/config.json` points to correct backend URL (use hostname/IP, not localhost for non-dev)

### Important Configuration Notes

**Frontend Backend URL**:
- The frontend `config.json` must specify the backend URL using the **actual hostname or IP address**
- **Do NOT use `localhost`** except for local development
- This is because the frontend runs in the browser, so "localhost" refers to the client's machine, not the server
- Example for production: `{"backendUrl": "http://192.168.1.100:8001"}`
- Example for local dev: `{"backendUrl": "http://localhost:8000"}`

**Redis (Required)**:
- Redis is **required** for the backend to function
- Used for WebSocket message broadcasting across all connected clients
- Local development: Start Redis with `docker run -d -p 6379:6379 redis:alpine`
- Docker testing: Redis is included by default in compose files
- Default connection: `localhost:6379` (configurable via environment variables)

## Time Expectations
- **Dependency installation**: 30 seconds. NEVER CANCEL.
- **Application startup**: 2-3 seconds. NEVER CANCEL.
- **Functional testing**: 2-3 minutes for complete validation scenario
- **Docker build**: Works on standard machines; may fail in restricted sandbox environments

## Requirements
- **Python 3.11+** (tested with Python 3.12.3)
- **Node.js 18+** for frontend development
- **Redis** (required for backend operation)
- **pip** for Python dependency management
- **npm** for JavaScript dependency management
- **Docker & Docker Compose** for containerized testing and deployment
- **Modern web browser** for functional testing
- **Network access** for installing packages (pip/npm install)

## Known Limitations
- **No automated test suite** - rely on manual functional testing
- **No linting configuration** - manual code review required
- **Backend split across multiple files** - main.py, connection_manager.py, redis_manager.py
- **Frontend config requires hostname/IP** - cannot use "localhost" for production deployments (frontend runs in browser)