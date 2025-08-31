# Remote Teleprompter

A modern microservices-based teleprompter application that enables real-time teleprompter control between devices. One device (computer) acts as a controller to edit scripts and manage playback, while another device (phone/tablet) displays the teleprompter text.

## Features

- **Remote Control**: Control teleprompter from any device with a web browser
- **Real-time Sync**: WebSocket-based communication for instant updates  
- **Microservices Architecture**: Scalable, modular design with separate services
- **Responsive Design**: Works on desktop, tablets, and mobile devices
- **Channel-based**: Multiple independent teleprompter sessions via named channels
- **Mirror Support**: Horizontal and vertical mirroring for teleprompter setup flexibility
- **Adjustable Settings**: Speed control, font size, and text width adjustment

## Architecture

The application is built using a microservices architecture with the following services:

- **Backend Service** (`services/backend/`): FastAPI backend providing WebSocket and REST APIs
- **Landing Service** (`services/landing/`): Vue.js application serving the main landing page
- **Controller Service** (`services/controller/`): Vue.js application for script editing and playback control
- **Teleprompter Service** (`services/teleprompter/`): Vue.js application for full-screen text display
- **Nginx Proxy**: Reverse proxy routing traffic to appropriate services

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
- **Main Application**: http://localhost:3000 (via Nginx proxy)
- **Landing Page**: http://localhost:80
- **Controller**: http://localhost:8080
- **Teleprompter**: http://localhost:8081
- **Backend API**: http://localhost:8001

### Usage
1. Open http://localhost:3000 in your web browser
2. Choose your mode:
   - **💻 Controller Mode**: For editing scripts and controlling playback
   - **📱 Teleprompter Mode**: For full-screen text display
3. Enter a channel name (both devices must use the same channel name)
4. Click "Connect to Channel"
5. In Controller mode: Edit your script and use the controls
6. In Teleprompter mode: The text will display and scroll automatically

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
