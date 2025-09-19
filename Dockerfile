# Unified Teleprompter Application Dockerfile
FROM python:3.11-slim

# Install Node.js for building the frontend
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy frontend source and build it
COPY frontend/package*.json ./backend/
COPY frontend/vite.config.js ./backend/
COPY frontend/index.html ./backend/
COPY frontend/src/ ./backend/src/

# Build frontend
WORKDIR /app/backend
RUN npm install && npm run build

# Copy built assets to the correct locations
RUN rm -rf static/assets templates/index.html || true && \
    mkdir -p static templates && \
    cp -r dist/assets static/ && \
    cp dist/index.html templates/

# Copy unified main.py
COPY main.py /app/

# Set working directory back to app root
WORKDIR /app

# Expose port
EXPOSE 8000

# Environment variables
ENV TELEPROMPTER_WS_URL=""
ENV TELEPROMPTER_UI_SUBPATH=""

# Run the application
CMD ["python", "main.py"]