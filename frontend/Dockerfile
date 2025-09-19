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
ARG BACKEND_URL=http://localhost:8001
ENV BACKEND_URL=$BACKEND_URL
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create a script to substitute environment variables at runtime
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-substitute-env.sh && \
    echo 'if [ -n "$BACKEND_URL" ]; then' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '  echo "Setting backend URL to: $BACKEND_URL"' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '  sed -i "s|%BACKEND_URL%|$BACKEND_URL|g" /usr/share/nginx/html/index.html' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo 'else' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '  echo "No BACKEND_URL provided, using default"' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo 'fi' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '# Check if config.json exists and is writable (mounted)' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo 'if [ ! -f "/usr/share/nginx/html/config.json" ]; then' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '  echo "No config.json found, creating default"' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '  echo "{\"backendUrl\":\"http://localhost:8001\"}" > /usr/share/nginx/html/config.json' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo 'else' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo '  echo "Using existing config.json"' >> /docker-entrypoint.d/30-substitute-env.sh && \
    echo 'fi' >> /docker-entrypoint.d/30-substitute-env.sh && \
    chmod +x /docker-entrypoint.d/30-substitute-env.sh

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]