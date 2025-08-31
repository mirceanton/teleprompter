# Remote Teleprompter

A web-based teleprompter application that enables real-time teleprompter control between devices. One device (computer) acts as a controller to edit scripts and manage playback, while another device (phone/tablet) displays the teleprompter text.

## Features

- **Remote Control**: Control teleprompter from any device with a web browser
- **Real-time Sync**: WebSocket-based communication for instant updates  
- **Dual Mode Interface**: Controller mode for editing and control, Teleprompter mode for display
- **Responsive Design**: Works on desktop, tablets, and mobile devices
- **Channel-based**: Multiple independent teleprompter sessions via named channels
- **Mirror Support**: Horizontal and vertical mirroring for teleprompter setup flexibility
- **Adjustable Settings**: Speed control, font size, and text width adjustment

## Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation & Running
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python3 main.py
```

The application will be available at http://localhost:8000

### Usage
1. Open http://localhost:8000 in your web browser
2. Choose your mode:
   - **💻 Controller Mode**: For editing scripts and controlling playback
   - **📱 Teleprompter Mode**: For full-screen text display
3. Enter a channel name (both devices must use the same channel name)
4. Click "Connect to Channel"
5. In Controller mode: Edit your script and use the controls
6. In Teleprompter mode: The text will display and scroll automatically
## API Endpoints

The application provides the following endpoints:

- **GET /**: Main application interface
- **GET /health**: Health check endpoint
- **WebSocket /ws/{channel}**: Real-time communication for teleprompter control
- **GET /static/**: Static assets (CSS, JavaScript)

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Communication**: WebSockets for real-time messaging
- **Styling**: CSS Grid and Flexbox for responsive design

## Development

### Making Changes
1. **Backend changes**: Edit `main.py` for API endpoints, WebSocket handling, or server configuration
2. **Frontend logic**: Edit `static/js/app.js` for UI behavior, WebSocket communication, or control logic  
3. **UI styling**: Edit `static/css/style.css` for visual appearance
4. **HTML structure**: Edit `templates/index.html` for layout or new UI elements
5. **Dependencies**: Edit `requirements.txt` for new Python packages

### Testing
After making changes:
1. Restart the application: `python3 main.py`
2. Test both Controller and Teleprompter modes
3. Verify WebSocket communication between modes
4. Check browser console for any JavaScript errors

## License

This project is licensed under the terms included in the LICENSE file.
