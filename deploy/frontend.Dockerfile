

# syntax=docker/dockerfile:1.6

# ------------------------------------------------------------
# 1) Builder: install deps and build static assets with Vite
# ------------------------------------------------------------
FROM node:22-alpine AS builder

# Avoid installing optional deps that might require native builds on NAS
ENV npm_config_only=production \
    CI=true

WORKDIR /app

# Copy only manifest first to leverage Docker layer cache
COPY frontend/package*.json ./

# Install exactly what's in the lockfile (faster and reproducible)
# If you are developing locally and need peer resolution, prefer fixing versions
# over using --legacy-peer-deps/--force.
RUN npm ci

# Copy the rest of the frontend sources and build
COPY frontend/ /app/
RUN npm run build


# ------------------------------------------------------------
# 2) Runtime: serve static files from a small nginx image
# ------------------------------------------------------------
FROM nginx:alpine AS runtime

# Create nginx config for SPA and non-root user in minimal layers
# nginx:alpine can run as non-root when listening on port >1024 (8080)
RUN <<'EOF' sh
set -eu
# Create nginx config for SPA (listening on non-privileged port 8080)
cat > /etc/nginx/conf.d/default.conf <<'NGINX_CONF'
server {
  listen       8080;
  server_name  _;

  gzip on;
  gzip_types text/plain text/css application/javascript application/json image/svg+xml;
  gzip_min_length 1024;

  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  # Cache static assets aggressively (filenames are content‑hashed by Vite)
  location ~* \.(?:js|css|svg|woff2?)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
    try_files $uri =404;
  }
}
NGINX_CONF
# Modify main nginx.conf for non-root operation (pid file in writable location)
sed -i 's|pid /var/run/nginx.pid;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf && \
sed -i 's|user  nginx;|# user  nginx;|' /etc/nginx/nginx.conf && \
# Create non-root user (UID/GID 101 matches docker-compose.yml)
addgroup -g 101 -S app && \
adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G app -g app app && \
# Create directories and set permissions for non-root nginx
mkdir -p /var/cache/nginx /var/log/nginx /var/run /tmp /usr/share/nginx/html && \
chown -R app:app /var/cache/nginx /var/log/nginx /var/run /tmp /usr/share/nginx/html /etc/nginx /usr/share/nginx
EOF

# Copy the build output from the builder stage
COPY --from=builder /app/dist/ /usr/share/nginx/html/
RUN chown -R app:app /usr/share/nginx/html

# Switch to non-root user
USER app

# Healthcheck is defined in docker-compose.yml
EXPOSE 8080

# Default command: nginx runs as non-root user (listening on port 8080)
CMD ["nginx", "-g", "daemon off;"]
