# Remote Teleprompter Microservices

A web-based teleprompter application split into microservices for better scalability and deployment flexibility.

## Architecture

The application is now split into 4 microservices:

### 🏠 Landing Page (`/`)
- **Technology**: Vue.js 3 + Vuetify 3
- **Port**: 80 (Docker) / 3000 (Development)
- **Purpose**: Room ID generation/input and role selection
- **Features**:
  - Generate random room IDs
  - Paste room IDs from clipboard
  - Select role (Controller or Teleprompter)
  - Redirect to appropriate microservice

### 💻 Controller App (`/controller`)
- **Technology**: Vue.js 3 + Vuetify 3
- **Port**: 8080 (Docker) / 3001 (Development)
- **Purpose**: Script editing and playback control
- **Features**:
  - Script editor with auto-sync
  - Playback controls (start/pause/reset/fast-forward)
  - Speed control
  - Text width and font size adjustment
  - Mirror controls
  - Connection monitoring

### 📱 Teleprompter App (`/teleprompter`)
- **Technology**: Vue.js 3 + Vuetify 3
- **Port**: 8081 (Docker) / 3002 (Development)
- **Purpose**: Text display with scrolling
- **Features**:
  - Fullscreen text display
  - Smooth scrolling
  - Mirror modes (horizontal/vertical)
  - Font size and width controls
  - Floating controls in fullscreen mode

### 📡 Backend API (`/api`)
- **Technology**: FastAPI + WebSockets
- **Port**: 8001
- **Purpose**: Real-time communication between services
- **Features**:
  - WebSocket communication (`/api/ws/{channel}`)
  - Channel management
  - Health check endpoint (`/api/health`)
  - CORS support for frontend apps

## Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Quick Start (Development)
```bash
# Make the dev script executable
chmod +x dev-start.sh

# Start all services in development mode
./dev-start.sh
```

This will start:
- Backend API: http://localhost:8001
- Landing Page: http://localhost:3000
- Controller: http://localhost:3001
- Teleprompter: http://localhost:3002

### Manual Development Setup

1. **Start Backend API**:
```bash
cd services/backend
pip install -r requirements.txt
python3 main.py
```

2. **Start Landing Page**:
```bash
cd services/landing
npm install
npm run dev
```

3. **Start Controller App**:
```bash
cd services/controller
npm install
npm run dev
```

4. **Start Teleprompter App**:
```bash
cd services/teleprompter
npm install
npm run dev
```

## Production Deployment

### Using Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d --build
```

Services will be available at:
- **Unified Access**: http://localhost:3000 (via nginx proxy)
  - Landing: http://localhost:3000/
  - Controller: http://localhost:3000/controller
  - Teleprompter: http://localhost:3000/teleprompter
  - API: http://localhost:3000/api
- **Direct Access**:
  - Landing: http://localhost:80
  - Controller: http://localhost:8080
  - Teleprompter: http://localhost:8081
  - Backend API: http://localhost:8001

### Individual Service Docker Build
```bash
# Backend API
docker build -t teleprompter-backend ./backend

# Landing Page
docker build -t teleprompter-landing ./landing

# Controller
docker build -t teleprompter-controller ./controller

# Teleprompter
docker build -t teleprompter-teleprompter ./teleprompter
```

## Usage

1. **Open Landing Page**: Navigate to the root URL
2. **Create/Join Room**: Generate a room ID or paste an existing one
3. **Select Role**: Choose "Controller" or "Teleprompter"
4. **Controller Setup**: 
   - Edit your script in the text editor
   - Use playback controls to manage scrolling
   - Adjust speed, font size, and mirror settings
5. **Teleprompter Setup**:
   - View the scrolling text
   - Use fullscreen mode for better visibility
   - Adjust local settings with floating controls

## API Endpoints

### Backend API (`/api`)
- `GET /api/health` - Health check
- `GET /api/channel/{channel}/info` - Get channel information
- `WebSocket /api/ws/{channel}` - Real-time communication

## Technology Stack

- **Frontend**: Vue.js 3, Vuetify 3, Vite
- **Backend**: FastAPI, WebSockets, uvicorn
- **Containerization**: Docker, nginx
- **Orchestration**: Docker Compose

## Migration from Monolith

The original monolithic application has been split while maintaining all functionality:
- ✅ Real-time WebSocket communication
- ✅ Multi-device synchronization
- ✅ Script editing and playback controls
- ✅ Mirror modes and display adjustments
- ✅ Multi-teleprompter support
- ✅ Responsive design

The new architecture provides:
- Better separation of concerns
- Independent scaling of services
- Easier deployment and maintenance
- Modern Vue.js frontend with Vuetify components
