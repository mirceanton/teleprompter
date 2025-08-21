# Remote Teleprompter

A modern web-based teleprompter application built with React and shadcn/ui components. Control your phone's teleprompter remotely from your computer with real-time synchronization.

## Features

- **Dual Mode Interface**: Switch between Controller and Teleprompter modes
- **Real-time Sync**: WebSocket-based communication for instant text and control synchronization
- **Modern UI**: Built with React, TypeScript, and shadcn/ui components
- **Responsive Design**: Works on desktop and mobile devices
- **Full Control**: Speed, text width, font size, and mirror controls
- **Professional Styling**: Clean, dark gradient interface optimized for recording

## Technology Stack

### Frontend
- **React 19** with TypeScript
- **shadcn/ui** components for modern, accessible UI
- **Tailwind CSS** for styling
- **Vite** for fast development and optimized builds
- **Custom WebSocket hook** for real-time communication

### Backend
- **FastAPI** (Python) for API endpoints
- **WebSocket** support for real-time communication
- **Static file serving** for the React application

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for development)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd teleprompter
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. For development, install Node.js dependencies:
```bash
npm install
```

### Running the Application

#### Production Mode (using built files)
```bash
python3 main.py
```
The application will be available at http://localhost:8000

#### Development Mode (with hot reload)
In one terminal, start the backend:
```bash
python3 main.py
```

In another terminal, start the frontend development server:
```bash
npm run dev
```
Frontend will be available at http://localhost:3000 with backend proxy

### Building for Production

To build the React application for production:
```bash
npm run build
```

This generates optimized static files in the `static/` directory that are served by FastAPI.

## Usage

1. **Open the application** in your browser
2. **Select mode**:
   - Choose "Controller Mode" on your computer
   - Choose "Teleprompter Mode" on your phone/tablet
3. **Enter a channel name** (same on both devices)
4. **Click "Connect to Channel"** on both devices
5. **Start teleprompting**:
   - Edit script on controller
   - Use playback controls (Start/Pause/Reset/etc.)
   - Adjust speed, text width, and font size
   - Enable mirror modes if needed

## Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Controller    │◄──────────────►│   Teleprompter  │
│   (Computer)    │                │   (Phone/Tablet)│
└─────────────────┘                └─────────────────┘
         │                                  │
         │              HTTP                │
         └──────────────────────────────────┘
                        │
                ┌───────────────┐
                │  FastAPI      │
                │  Backend      │
                │  (Python)     │
                └───────────────┘
```

### Key Components

- **App.tsx**: Main React component with state management
- **useWebSocket.ts**: Custom hook for WebSocket communication
- **shadcn/ui components**: Modern, accessible UI components
- **main.py**: FastAPI backend with WebSocket endpoints
- **static/**: Built React application files

## Development

### Project Structure
```
teleprompter/
├── src/                     # React source code
│   ├── components/ui/       # shadcn/ui components
│   ├── hooks/              # Custom React hooks
│   ├── App.tsx             # Main application component
│   └── main.tsx            # React entry point
├── static/                 # Built application (served by FastAPI)
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

### API Endpoints

- `GET /` - Serve the React application
- `GET /health` - Health check endpoint
- `WebSocket /ws/{channel}` - Real-time communication endpoint

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.
