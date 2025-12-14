# Security Deployment Baseline

> This document defines the security baseline for ZenetHunter production deployments. All deployments should meet or exceed these requirements.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Security Requirements](#2-security-requirements)
3. [Implementation Checklist](#3-implementation-checklist)
4. [Verification](#4-verification)
5. [Compliance](#5-compliance)

---

## 1. Overview

This security baseline ensures that ZenetHunter deployments follow industry best practices for containerized applications. The baseline covers:

- **Health Checks**: Comprehensive health monitoring
- **Resource Limits**: CPU and memory constraints
- **Least Privilege**: Non-root execution, minimal capabilities
- **Network Security**: Isolation and access controls
- **File System Security**: Read-only root, controlled writable areas

---

## 2. Security Requirements

### 2.1 Health Checks

**Requirement**: All services must have health checks configured.

**Implementation**:
- ✅ **Database**: `pg_isready` check every 10s
- ✅ **Backend**: HTTP health check on `/healthz` with 3s timeout
- ✅ **Frontend**: HTTP check on root path with 3s timeout

**Rationale**: Health checks enable automatic recovery and prevent traffic to unhealthy containers.

### 2.2 Resource Limits

**Requirement**: All containers must have CPU and memory limits.

**Implementation**:

| Service | CPU Limit | Memory Limit | CPU Reservation | Memory Reservation |
|---------|----------|--------------|-----------------|---------------------|
| Backend | 2.0 cores | 2GB | 0.5 cores | 512MB |
| Frontend | 1.0 core | 512MB | 0.25 cores | 128MB |
| Database | 1.5 cores | 1GB | 0.25 cores | 256MB |

**Rationale**: Resource limits prevent resource exhaustion attacks and ensure fair resource sharing.

### 2.3 Least Privilege

**Requirement**: All containers must run as non-root users with minimal capabilities.

**Implementation**:

#### User Configuration
- ✅ **Backend**: UID/GID 101:101 (non-root)
- ✅ **Frontend**: UID/GID 101:101 (non-root)
- ✅ **Database**: PostgreSQL default user (non-root)

#### Capability Management
- ✅ **Backend**: Drop ALL, add only `NET_BIND_SERVICE`
- ✅ **Frontend**: Drop ALL, add only `NET_BIND_SERVICE`
- ✅ **Database**: Drop ALL, add required PostgreSQL capabilities

#### Privilege Escalation
- ✅ **Backend**: `no-new-privileges:true`
- ✅ **Frontend**: `no-new-privileges:true`

**Rationale**: Non-root execution and minimal capabilities reduce attack surface and limit potential damage from container compromise.

### 2.4 File System Security

**Requirement**: Containers should use read-only root filesystem where possible.

**Implementation**:
- ✅ **Backend**: `read_only: true` with `tmpfs: /tmp`
- ✅ **Frontend**: `read_only: true` with `tmpfs: /tmp, /var/cache/nginx, /var/run`
- ⚠️ **Database**: Read-only not suitable (requires write access to data directory)

**Rationale**: Read-only filesystem prevents unauthorized file modifications and reduces attack surface.

### 2.5 Network Security

**Requirement**: Network isolation and controlled access.

**Implementation**:
- ✅ **Internal Network**: Services communicate via isolated bridge network
- ✅ **Database**: Not exposed to host (internal only)
- ✅ **Port Mapping**: Only necessary ports exposed (8000, 1226)
- ✅ **Network Isolation**: IPAM configuration for subnet control

**Rationale**: Network isolation limits lateral movement and reduces attack surface.

### 2.6 Environment Security

**Requirement**: Secure environment variable handling.

**Implementation**:
- ✅ **Secrets**: Never commit secrets to repository
- ✅ **Environment Variables**: Use `.env` files (not committed)
- ✅ **Python Security**: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
- ✅ **PostgreSQL**: SCRAM-SHA-256 authentication

**Rationale**: Proper secret management prevents credential leaks.

---

## 3. Implementation Checklist

### Pre-Deployment

- [ ] Review all resource limits for your hardware
- [ ] Configure `.env` file with secure secrets
- [ ] Verify network isolation requirements
- [ ] Review firewall rules for exposed ports
- [ ] Ensure Docker daemon security settings

### Deployment

- [ ] Verify all services start with non-root users
- [ ] Confirm health checks are working
- [ ] Test resource limits (stress test)
- [ ] Verify read-only filesystem (attempt write to root)
- [ ] Confirm network isolation (test inter-container communication)
- [ ] Verify capability restrictions (test privilege escalation)

### Post-Deployment

- [ ] Monitor resource usage
- [ ] Review security logs
- [ ] Verify health check responses
- [ ] Test service recovery after failures
- [ ] Review container logs for security warnings

---

## 4. Verification

### 4.1 Automated Verification

Use the provided test script to verify security configuration:

```bash
./deploy/test_security.sh
```

### 4.2 Manual Verification

#### Check Non-Root Execution

```bash
# Verify backend runs as non-root
docker compose exec backend id
# Expected: uid=101(app) gid=101(app)

# Verify frontend runs as non-root
docker compose exec frontend id
# Expected: uid=101(app) gid=101(app)
```

#### Check Resource Limits

```bash
# View resource usage
docker stats

# Verify limits are applied
docker inspect zh-backend | jq '.[0].HostConfig.Memory'
docker inspect zh-backend | jq '.[0].HostConfig.CpuQuota'
```

#### Check Read-Only Filesystem

```bash
# Attempt to write to root (should fail)
docker compose exec backend touch /test.txt
# Expected: Read-only file system error

# Verify tmpfs is writable
docker compose exec backend touch /tmp/test.txt
# Expected: Success
```

#### Check Capabilities

```bash
# Verify capabilities
docker inspect zh-backend | jq '.[0].HostConfig.CapDrop'
docker inspect zh-backend | jq '.[0].HostConfig.CapAdd'
# Expected: CapDrop: ["ALL"], CapAdd: ["NET_BIND_SERVICE"]
```

#### Check Health Checks

```bash
# Verify health check status
docker compose ps
# All services should show "healthy"

# Test health endpoints
curl http://localhost:8000/healthz
curl http://localhost:1226/
```

#### Check Network Isolation

```bash
# Verify database is not exposed to host
netstat -tlnp | grep 5432
# Expected: No output (database not exposed)

# Verify inter-container communication
docker compose exec backend ping -c 1 db
# Expected: Success (internal network works)
```

---

## 5. Compliance

### 5.1 Security Standards

This baseline aligns with:

- **CIS Docker Benchmark**: Container security best practices
- **OWASP Container Security**: Secure container deployment
- **Docker Security Best Practices**: Official Docker recommendations
- **12-Factor App**: Configuration and security principles

### 5.2 Compliance Levels

#### Minimum (Required)
- Non-root user execution
- Resource limits configured
- Health checks enabled
- Network isolation

#### Recommended (Best Practice)
- All minimum requirements
- Read-only filesystem
- Capability restrictions
- Privilege escalation disabled
- Comprehensive health checks

#### Enhanced (High Security)
- All recommended requirements
- AppArmor/SELinux profiles
- Seccomp profiles
- Network policies
- Regular security scanning

### 5.3 Security Updates

- **Base Images**: Update regularly (monthly recommended)
- **Dependencies**: Update via automated dependency scanning
- **Security Patches**: Apply critical patches immediately
- **Vulnerability Scanning**: Regular container image scanning

---

## Appendix

### A. Security Configuration Reference

#### docker-compose.yml Security Settings

```yaml
services:
  service_name:
    # Non-root user
    user: "101:101"

    # Read-only filesystem
    read_only: true
    tmpfs:
      - /tmp

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

    # Capability management
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # Disable privilege escalation
    security_opt:
      - no-new-privileges:true

    # Health check
    healthcheck:
      test: ["CMD", "health-check-command"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
```

### B. Security Testing Commands

```bash
# Test resource limits
docker run --rm -it --cpus="0.5" --memory="512m" stress-ng --cpu 1 --timeout 60s

# Test read-only filesystem
docker run --rm --read-only alpine touch /test
# Expected: Error

# Test capability restrictions
docker run --rm --cap-drop=ALL --cap-add=NET_BIND_SERVICE alpine ping 8.8.8.8
# Expected: Permission denied (no NET_RAW capability)
```

### C. Security Monitoring

```bash
# Monitor resource usage
docker stats --no-stream

# Check container security settings
docker inspect <container> | jq '.[0].HostConfig'

# Monitor health check failures
docker events --filter 'health_status=unhealthy'

# Check for privilege escalation attempts
docker logs <container> | grep -i "permission\|privilege\|root"
```

---

**Last Updated**: 2024-12-09  
**Version**: 1.0  
**Applicable To**: ZenetHunter v0.1.0+
