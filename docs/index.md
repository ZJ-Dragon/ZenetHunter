# ZenetHunter Documentation

> Complete documentation for ZenetHunter Active Defense Platform

---

## 📚 Documentation Structure

### 🏠 Root Documentation

Essential documents in the project root:

- **[README.md](../README.md)** / **[README.zh-CN.md](../README.zh-CN.md)** - Project overview
- **[README-MACOS.md](../README-MACOS.md)** / **[zh-CN](../README-MACOS.zh-CN.md)** - macOS setup
- **[README-WINDOWS.md](../README-WINDOWS.md)** / **[zh-CN](../README-WINDOWS.zh-CN.md)** - Windows setup
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** / **[zh-CN](../CONTRIBUTING.zh-CN.md)** - Contribution guide
- **[SECURITY.md](../SECURITY.md)** / **[zh-CN](../SECURITY.zh-CN.md)** - Security policy
- **[LICENSE](../LICENSE)** - MIT License

---

## 📖 Technical Documentation

### Active Defense Module

- **[Active Defense README](active-defense/README.md)** / **[中文](active-defense/README.zh-CN.md)**
  - Complete technical documentation
  - All 14 operation types explained
  - Usage examples and safety guidelines

### API Reference

- **[API Documentation](api/README.md)** / **[中文](api/README.zh-CN.md)**
  - Complete REST API reference
  - WebSocket events
  - Authentication guide
  - Error handling

### Configuration

- **[Environment Variables](ENVIRONMENT.md)** / **[中文](ENVIRONMENT.zh-CN.md)**
  - Complete list of all environment variables
  - Configuration file location and syntax
  - Production deployment checklist
  - Troubleshooting guide

- **[System Environment Variables](SYSTEM_ENV.md)** / **[中文](SYSTEM_ENV.zh-CN.md)**
  - System-level environment variables (Python, OS, Shell)
  - Environment detection and priority
  - Root privileges and permissions
  - Docker container detection
  - Troubleshooting system variables

### Engine Implementation

- **[Engine Technical Docs](../backend/app/core/engine/README.md)** / **[中文](../backend/app/core/engine/README.zh-CN.md)**
  - Low-level implementation details
  - Scapy engine architecture
  - Platform-specific code

---

## 📊 Reports

Project reports and audit documents:

- **[Active Defense Refactor](reports/ACTIVE_DEFENSE_REFACTOR.md)** - v2.0 refactoring overview
- **[Codebase Audit](reports/CODEBASE_AUDIT.md)** - Code quality audit
- **[Project Audit Checklist](reports/PROJECT_AUDIT_CHECKLIST.md)** - Completeness audit
- **[Project Completion Report](reports/PROJECT_COMPLETION_REPORT.md)** - Final status
- **[Project Summary](reports/PROJECT_SUMMARY.md)** - Executive summary
- **[Session Summary](reports/SESSION_SUMMARY.md)** - Complete session report
- **[Documentation Summary](reports/DOCUMENTATION_SUMMARY.md)** - Docs overview
- **[Scan Fix Report](reports/SCAN_FIX_REPORT.md)** - Original scan issues
- **[Scan Performance Fix](reports/SCAN_PERFORMANCE_FIX.md)** - Performance optimization

---

## 📘 Setup Guides

Installation and configuration guides:

- **[Conda Setup](guides/CONDA_SETUP.md)** - Conda environment configuration
- **[Environment Setup](guides/ENVIRONMENT_SETUP.md)** - Smart environment detection
- **[Force Shutdown Guide](guides/FORCE_SHUTDOWN_GUIDE.md)** - Shutdown mechanisms

---

## 🔧 Troubleshooting

Problem-solving guides and fixes:

- **[Quick Fix Guide](troubleshooting/QUICK_FIX_GUIDE.md)** - Common issues quick reference
- **[Import Errors Fix](troubleshooting/IMPORT_ERRORS_FIX.md)** - Module import issues
- **[IDE Import Fix](troubleshooting/IDE_IMPORT_FIX.md)** - IDE configuration
- **[Port Fix Guide](troubleshooting/PORT_FIX_GUIDE.md)** - Port occupation issues
- **[Database Migration](troubleshooting/DATABASE_MIGRATION_REQUIRED.md)** - Schema migration
- **[CLI Shutdown Fix](troubleshooting/CLI_SHUTDOWN_FIX.md)** - Ctrl+C handling
- **[Shutdown Optimization](troubleshooting/SHUTDOWN_OPTIMIZATION.md)** - Graceful shutdown
- **[Final Fixes Summary](troubleshooting/FINAL_FIXES_SUMMARY.md)** - All fixes overview

---

## 🚀 Quick Links

### For New Users

1. **[Getting Started](../README.md#quick-start)** - Installation and first run
2. **[API Documentation](api/README.md)** - Using the REST API
3. **[Quick Fix Guide](troubleshooting/QUICK_FIX_GUIDE.md)** - Common problems

### For Developers

1. **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute
2. **[Active Defense Docs](active-defense/README.md)** - Technical details
3. **[Engine Implementation](../backend/app/core/engine/README.md)** - Low-level code

### For Deployers

1. **[Deployment Guide](../deploy/README.md)** - Production deployment
2. **[Security Baseline](../deploy/SECURITY_BASELINE.md)** - Security configuration
3. **[Network Setup](../deploy/NETWORK-SETUP.md)** - Network configuration

---

## 📂 Repository Structure

```
ZenetHunter/
├── README.md / README.zh-CN.md          # Project overview
├── CHANGELOG.md                         # Version history
├── CONTRIBUTING.md                      # Contribution guide
├── SECURITY.md                          # Security policy
│
├── docs/
│   ├── index.md                         # This file
│   ├── active-defense/                  # Active defense module docs
│   ├── api/                             # API reference
│   ├── reports/                         # Project reports ⭐
│   ├── guides/                          # Setup guides ⭐
│   └── troubleshooting/                 # Problem-solving ⭐
│
├── backend/                             # Python backend
├── frontend/                            # React frontend
├── deploy/                              # Deployment configs
│
├── cleanup.sh                           # Cleanup script ⭐
├── fix-imports.sh                       # IDE fix script ⭐
└── start-local.sh                       # Startup script
```

---

## 🆕 Recent Updates

- **2026-01-23**: Documentation reorganization
  - Moved 19 docs to structured folders
  - Created reports/guides/troubleshooting sections
  - Added cleanup and fix-imports scripts

- **2026-01-17**: Active Defense Refactor (v2.0)
  - Removed passive defense modules
  - Implemented 14 active defense techniques
  - Complete performance optimization

---

## 📝 Documentation Guidelines

### File Naming

- **English**: `README.md`, `GUIDE_NAME.md`
- **Chinese**: `README.zh-CN.md`, `GUIDE_NAME.zh-CN.md`

### Location

- **Root**: Core project docs (README, CHANGELOG, etc.)
- **docs/reports/**: Project status and audit reports
- **docs/guides/**: Installation and setup guides
- **docs/troubleshooting/**: Problem-solving documentation
- **docs/api/**: API reference
- **docs/active-defense/**: Module-specific technical docs

---

## 🔗 External Resources

- **GitHub**: https://github.com/ZJ-Dragon/ZenetHunter
- **Issues**: https://github.com/ZJ-Dragon/ZenetHunter/issues
- **Discussions**: https://github.com/ZJ-Dragon/ZenetHunter/discussions

---

**Last Updated**: 2026-01-23  
**Documentation Version**: 2.0  
**Project Version**: 2.0.0 (Active Defense Refactor)
