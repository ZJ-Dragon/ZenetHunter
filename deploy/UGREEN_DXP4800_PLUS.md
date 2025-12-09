# UGREEN DXP4800 Plus Deployment Guide

> This guide provides detailed instructions and best practices for deploying ZenetHunter on **UGREEN NASync DXP4800 Plus (UGOS Pro)**.

---

## Table of Contents

1. [Hardware Specifications](#1-hardware-specifications)
2. [System Requirements](#2-system-requirements)
3. [Prerequisites](#3-prerequisites)
4. [Deployment Methods](#4-deployment-methods)
5. [Storage Optimization](#5-storage-optimization)
6. [Network Configuration](#6-network-configuration)
7. [Performance Tuning](#7-performance-tuning)
8. [Troubleshooting](#8-troubleshooting)
9. [Maintenance & Upgrades](#9-maintenance--upgrades)
10. [Reference Resources](#10-reference-resources)

---

## 1. Hardware Specifications

### DXP4800 Plus Key Specifications

- **CPU**: Intel® Pentium® Gold 8505 (5 cores / 6 threads)
- **Memory**: 8GB DDR5 (expandable to 64GB)
- **Storage Interfaces**:
  - 4× SATA 3.5"/2.5" drive bays
  - 2× M.2 NVMe SSD slots (2280)
- **Network**: 2× 2.5GbE ports (supports link aggregation)
- **Operating System**: UGOS Pro (Linux-based)

### Performance Characteristics

- **CPU Performance**: Suitable for lightweight container workloads, recommend limiting CPU-intensive tasks
- **Memory**: 8GB is sufficient for running multiple containers, recommend reserving at least 2GB for Docker
- **Storage**: M.2 SSD provides optimal performance, recommend storing Docker data on SSD

---

## 2. System Requirements

### UGOS Pro Requirements

- **System Version**: UGOS Pro (latest stable release)
- **Docker**: Install Docker app via App Center
- **SSH**: Enable SSH access (for command-line deployment)
- **Storage Space**: At least 10GB free space (SSD recommended)

### Network Requirements

- **LAN Access**: Ensure NAS and deployment device are on the same local network
- **Port Availability**: Ensure ports 8000, 1226 are not in use
- **Firewall**: If firewall is enabled, open corresponding ports

---

## 3. Prerequisites

### 3.1 Enable SSH

1. Log in to UGOS Pro management interface
2. Go to **System Settings** → **SSH**
3. Enable SSH service
4. Note SSH port (default 22)

### 3.2 Install Docker

1. Open **App Center**
2. Search and install **Docker** app
3. Wait for installation to complete and start Docker service
4. Verify installation:
   ```bash
   docker --version
   docker compose version
   ```

### 3.3 Prepare Storage

**Important**: Store Docker data on M.2 SSD for optimal performance.

1. Create storage pool in UGOS Pro (if not already created)
2. Ensure at least one M.2 SSD is available
3. Create shared folder on SSD (e.g., `/mnt/ssd/docker`)
4. Configure Docker data directory to point to SSD (optional, via Docker settings)

> **Community Recommendation**: Configure Docker app data directory on SSD to avoid HDD spinning and improve responsiveness.

---

## 4. Deployment Methods

### Method A: SSH Command-Line Deployment (Recommended)

#### Step 1: Get Project Code

```bash
# SSH into NAS
ssh admin@<NAS-IP>

# Choose storage location (recommend shared folder on SSD)
cd /mnt/ssd/projects  # or your chosen path

# Clone project
git clone https://github.com/ZJ-Dragon/ZenetHunter.git
cd ZenetHunter
```

#### Step 2: Configure Environment Variables

```bash
cd deploy

# Create environment variable file
cp env/.env.example env/.env

# Edit environment variables
vi env/.env  # or use your preferred editor
```

**Key Configuration Items**:

```bash
# Environment settings
APP_ENV=production

# CORS configuration (use NAS IP)
CORS_ALLOW_ORIGINS=http://<NAS-IP>:1226,http://<NAS-IP>:8080

# Database configuration (use service name 'db')
DATABASE_URL=postgresql://zenethunter:zenethunter@db:5432/zenethunter

# Log level
LOG_LEVEL=info
```

#### Step 3: Build and Start

```bash
# Build images (first deployment or after code updates)
docker compose build

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

#### Step 4: Verify Deployment

```bash
# Check health status
curl http://localhost:8000/healthz

# Or access from other devices on LAN
curl http://<NAS-IP>:8000/healthz
```

**Access URLs**:
- Frontend: `http://<NAS-IP>:1226`
- Backend API: `http://<NAS-IP>:8000`
- API Documentation: `http://<NAS-IP>:8000/docs`

### Method B: Portainer UI Deployment

#### Step 1: Install Portainer

1. Search for **Portainer** in App Center
2. Install and start Portainer
3. Access Portainer Web UI: `http://<NAS-IP>:9000`
4. Complete initial setup

#### Step 2: Create Stack

1. In Portainer, go to **Stacks** → **Add stack**
2. Name: `zenethunter`
3. Select **Web editor**
4. Paste contents of `deploy/docker-compose.yml` into editor
5. Configure environment variables (in **Environment variables** section)
6. Click **Deploy the stack**

#### Step 3: Verify Deployment

1. Check **Containers** status in Portainer
2. All containers should show as **Running**
3. Check **Logs** to confirm no errors

---

## 5. Storage Optimization

### 5.1 Docker Data Directory Configuration

**Recommended**: Configure Docker data directory on SSD.

1. Stop Docker service
2. In UGOS Pro settings, point Docker data directory to SSD path
3. Restart Docker service

### 5.2 Volume Mapping Optimization

In `docker-compose.yml`, you can customize volume mapping location:

```yaml
volumes:
  db_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/ssd/docker/zenethunter/db_data
```

### 5.3 Storage Pool Recommendations

- **SSD Storage Pool**: For Docker data, database, logs
- **HDD Storage Pool**: For large files, backups, archive data

---

## 6. Network Configuration

### 6.1 Port Mapping

Default port configuration:

| Service | Container Port | Host Port | Description |
|---------|----------------|-----------|-------------|
| Backend | 8000 | 8000 | API service |
| Frontend | 8080 | 1226 | Web interface |
| Database | 5432 | - | Internal network |

### 6.2 Firewall Configuration

If UGOS Pro firewall is enabled:

1. Go to **System Settings** → **Firewall**
2. Add rules:
   - Port 8000 (TCP) - Backend API
   - Port 1226 (TCP) - Frontend interface
3. Save and apply

### 6.3 Link Aggregation (Optional)

DXP4800 Plus supports dual 2.5GbE link aggregation:

1. Go to **Network Settings** → **Link Aggregation**
2. Configure both ports in aggregation mode
3. Increase network bandwidth (suitable for multi-user access)

---

## 7. Performance Tuning

### 7.1 CPU Limits

Considering DXP4800 Plus CPU performance, recommend limiting container resources:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'  # Limit to maximum 2 CPU cores
          memory: 2G
        reservations:
          cpus: '0.5'  # Guarantee at least 0.5 cores
          memory: 512M
```

### 7.2 Worker Process Configuration

Backend Uvicorn worker process recommendations:

- **Single Process Mode** (default): Suitable for lightweight loads
- **Multi-Process Mode**: For higher concurrency, can set `--workers 2` (maximum 2)

> **Note**: DXP4800 Plus has 5 cores / 6 threads, recommend worker count not exceeding 2.

### 7.3 Scanner Intervals

Network scanning tasks should use conservative intervals:

- Device scanning: Every 5-10 minutes
- Topology discovery: Every 15-30 minutes
- Avoid frequent scanning causing high CPU load

### 7.4 Database Optimization

PostgreSQL configuration recommendations (in `docker-compose.yml`):

```yaml
db:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_MAINTENANCE_WORK_MEM: 64MB
```

---

## 8. Troubleshooting

### 8.1 Service Won't Start

**Issue**: Container exits immediately after starting

**Troubleshooting Steps**:
```bash
# View container logs
docker compose logs <service-name>

# Check container status
docker compose ps

# Check resource usage
docker stats
```

**Common Causes**:
- Port already in use
- Insufficient memory
- Configuration file error
- Permission issues

### 8.2 Frontend Cannot Access Backend API

**Issue**: Frontend shows API errors

**Troubleshooting Steps**:
1. Check backend health status: `curl http://<NAS-IP>:8000/healthz`
2. Check CORS configuration: Ensure `CORS_ALLOW_ORIGINS` includes frontend URL
3. Check network connection: `docker compose exec backend ping db`

### 8.3 Database Connection Failed

**Issue**: Backend cannot connect to database

**Troubleshooting Steps**:
```bash
# Check database container status
docker compose ps db

# View database logs
docker compose logs db

# Test database connection
docker compose exec backend python -c "import psycopg2; psycopg2.connect('postgresql://zenethunter:zenethunter@db:5432/zenethunter')"
```

### 8.4 Performance Issues

**Issue**: System responds slowly

**Optimization Recommendations**:
1. Move Docker data to SSD
2. Reduce worker process count
3. Increase scanner intervals
4. Check for other high-load applications

### 8.5 Insufficient Storage Space

**Issue**: Disk space insufficient

**Cleanup Steps**:
```bash
# Clean unused images
docker image prune -a

# Clean unused volumes
docker volume prune

# Clean build cache
docker builder prune
```

---

## 9. Maintenance & Upgrades

### 9.1 Daily Maintenance

**Regular Tasks**:
- Check service status: `docker compose ps`
- View logs: `docker compose logs --tail=100`
- Clean log files (if file logging enabled)
- Backup database (important data)

### 9.2 Upgrade Procedure

```bash
# 1. Backup current configuration and data
cp -r deploy/env/.env deploy/env/.env.backup
docker compose exec db pg_dump -U zenethunter zenethunter > backup.sql

# 2. Pull latest code
git pull origin main

# 3. Rebuild images
docker compose build

# 4. Restart services (zero-downtime upgrade)
docker compose up -d --no-deps --build backend frontend

# 5. Verify services
docker compose ps
curl http://localhost:8000/healthz
```

### 9.3 Rollback

If issues occur after upgrade:

```bash
# Restore configuration
cp deploy/env/.env.backup deploy/env/.env

# Use previous image tag (if tagged)
docker compose pull
docker compose up -d

# Or restore database backup
docker compose exec -T db psql -U zenethunter zenethunter < backup.sql
```

---

## 10. Reference Resources

### Official Resources

- **UGREEN Website**: https://www.ugreen.com
- **DXP4800 Plus Product Page**: https://www.ugreen.com/products/usa-35260a
- **UGOS Pro Documentation**: Access via UGOS Pro management interface

### Community Resources

- **UGREEN Community Forum**: Search for "DXP4800 Plus" related discussions
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **Portainer Documentation**: https://docs.portainer.io/

### Technical Support

- **UGREEN Technical Support**: Contact via official website
- **Project Issues**: https://github.com/ZJ-Dragon/ZenetHunter/issues

---

## Appendix

### A. Quick Reference Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Check service status
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Enter container
docker compose exec backend bash
docker compose exec db psql -U zenethunter zenethunter
```

### B. Complete Environment Variables List

Refer to `deploy/env/.env.example` for complete environment variables list.

### C. Performance Monitoring

```bash
# View resource usage
docker stats

# View system resources
htop  # if installed

# View disk usage
df -h
docker system df
```

---

**Last Updated**: 2024-12-09  
**Applicable Version**: ZenetHunter v0.1.0+  
**UGOS Pro Version**: Latest stable release
