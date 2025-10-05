

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

# Optional: tune Nginx for SPA and static assets
# We replace the default site with a minimal config that:
# - serves files from /usr/share/nginx/html
# - falls back to index.html for client‑side routing (SPA)
# - enables basic gzip for text assets
RUN <<'EOF' bash
set -eu
cat > /etc/nginx/conf.d/default.conf <<'NGINX_CONF'
server {
  listen       80;
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
EOF

# Copy the build output from the builder stage
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Healthcheck is defined in docker-compose.yml
EXPOSE 80

# Default command (inherited): nginx -g 'daemon off;'
