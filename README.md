# Remote Teleprompter

A modern teleprompter application that enables real-time teleprompter control between devices. One device (computer) acts as a controller to edit scripts and manage playback, while another device (phone/tablet) displays the teleprompter text.

## Features

- **Remote Control**: Control teleprompter from any device with a web browser
- **Real-time Sync**: WebSocket-based communication for instant updates  
- **Single Page Application**: Unified Vue.js frontend with configurable backend URL
- **Responsive Design**: Works on desktop, tablets, and mobile devices
- **Channel-based**: Multiple independent teleprompter sessions via named channels
- **Mirror Support**: Horizontal and vertical mirroring for teleprompter setup flexibility
- **Adjustable Settings**: Speed control, font size, and text width adjustment

## Architecture

The application uses a simplified architecture with:

- **Backend Service** (`backend/`): FastAPI backend providing WebSocket and REST APIs
- **Frontend Service** (`frontend/`): Unified Vue.js application with Vue Router for all pages (landing, controller, teleprompter)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for backend development)

### Installation & Running

```bash
# Clone the repository
git clone https://github.com/mirceanton/teleprompter.git
cd teleprompter

# Start all services using Docker Compose
docker-compose up -d
```

The application will be available at:
- **Main Application**: http://localhost:3000
- **Backend API**: http://localhost:8001

### Configuration

The frontend can be configured to use a different backend URL via environment variables:

```bash
# Set custom backend URL
export FRONTEND_BACKEND_URL=http://my-backend-server:8001
docker-compose up -d
```

### Usage
1. Open http://localhost:3000 in your web browser
2. Enter a room ID or generate one
3. Choose your role:
   - **💻 Controller**: For editing scripts and controlling playback
   - **📱 Teleprompter**: For full-screen text display
4. Click "Join Room"
5. In Controller mode: Edit your script and use the playback controls
6. In Teleprompter mode: The text will display and scroll based on controller commands

## API Endpoints

The backend service provides the following endpoints:

- **GET /api/health**: Health check endpoint
- **WebSocket /api/ws/{channel}**: Real-time communication for teleprompter control

## Technology Stack

- **Backend**: FastAPI (Python) with WebSocket support
- **Frontend**: Vue.js 3 with Vite for modern JavaScript tooling
- **Communication**: WebSockets for real-time messaging
- **Infrastructure**: Docker, Docker Compose, Nginx reverse proxy
- **Styling**: Modern CSS with responsive design

## Development

### Making Changes

Each service can be developed independently:

1. **Backend changes**: 
   - Navigate to `services/backend/`
   - Edit `main.py` for API endpoints, WebSocket handling
   - Edit `requirements.txt` for Python dependencies

2. **Frontend services changes**:
   - Navigate to `services/landing/`, `services/controller/`, or `services/teleprompter/`
   - Edit Vue.js components in `src/`
   - Edit `package.json` for Node.js dependencies

### Development Workflow

```bash
# Start all services for development
docker-compose up -d

# For frontend development with hot reload
cd services/controller  # or landing/teleprompter
npm install
npm run dev

# For backend development
cd services/backend
pip install -r requirements.txt
python main.py
```

### Testing
After making changes:
1. Rebuild affected services: `docker-compose build <service-name>`
2. Restart services: `docker-compose restart`
3. Test through the main proxy at http://localhost:3000
4. Verify WebSocket communication between controller and teleprompter modes

## License

This project is licensed under the terms included in the LICENSE file.
