# Frontend Dockerfile for unified teleprompter application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create a script to ensure config.json exists
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-create-config.sh && \
    echo '# Check if config.json exists and is writable (mounted)' >> /docker-entrypoint.d/30-create-config.sh && \
    echo 'if [ ! -f "/usr/share/nginx/html/config.json" ]; then' >> /docker-entrypoint.d/30-create-config.sh && \
    echo '  echo "No config.json found, creating default"' >> /docker-entrypoint.d/30-create-config.sh && \
    echo '  echo "{\"backendUrl\":\"http://localhost:8001\"}" > /usr/share/nginx/html/config.json' >> /docker-entrypoint.d/30-create-config.sh && \
    echo 'else' >> /docker-entrypoint.d/30-create-config.sh && \
    echo '  echo "Using existing config.json"' >> /docker-entrypoint.d/30-create-config.sh && \
    echo 'fi' >> /docker-entrypoint.d/30-create-config.sh && \
    chmod +x /docker-entrypoint.d/30-create-config.sh

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]