# =================================================================================================
# Builder Stage
# =================================================================================================
FROM docker.io/node:24-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# =================================================================================================
# Production Stage
# =================================================================================================
FROM docker.io/nginx:1.29.1-alpine-slim

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public/config.json /usr/share/nginx/html/config.json

CMD ["nginx", "-g", "daemon off;"]
