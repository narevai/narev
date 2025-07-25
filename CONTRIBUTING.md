# Contributing to NarevAI

Thank you for your interest in contributing to NarevAI! We welcome contributions from developers, FinOps professionals, and anyone interested in improving AI cost analytics.

## Ways to Contribute

- 🐛 **Report bugs** via [GitHub Issues](https://github.com/narevai/narev/issues)
- 💡 **Suggest features** for better AI cost tracking
- 📚 **Improve documentation** 
- 🔧 **Submit code changes**
- 🧪 **Add test coverage**

## Before You Start

1. Check existing [issues](https://github.com/narevai/narev/issues) and [PRs](https://github.com/narevai/narev/pulls)
2. Read our [Code of Conduct](CODE_OF_CONDUCT.md)
3. For large changes, open an issue first to discuss

## Contribution Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** (see Development Setup below)
4. **Test your changes** using the make commands
5. **Submit a pull request**

# Development Environment Setup

## Prerequisites

- **VS Code** with **Dev Containers** extension
- **Docker Desktop** running
- Git access to the repository

## Setup

1. Clone the repository
```bash
git clone https://github.com/narevai/narev.git
cd narev
```
2. Open in VS Code
```bash
bashcode .
```

3. Choose Your Development Environment

You have three options for development:

### Option A: Frontend Development (Recommended for React/TypeScript work)
- VS Code will show a notification: "Reopen in Container"
- Or use Command Palette (Cmd/Ctrl+Shift+P): **Dev Containers: Reopen in Container**
- Select **"Narev Frontend Development"**
- This connects to the frontend container with proper TypeScript/React support

### Option B: Backend Development (Recommended for Python/API work)
- Use Command Palette (Cmd/Ctrl+Shift+P): **Dev Containers: Reopen in Container**
- Select **"Narev Backend Development"**
- This connects to the backend container with proper Python/Ruff support

### Option C: Full-Stack Development (Both Frontend & Backend)
For simultaneous frontend and backend development:

1. **Open first VS Code window** for frontend:
   - Command Palette → "Dev Containers: Reopen in Container"
   - Select **"Narev Frontend Development"**

2. **Open second VS Code window** for backend:
   - `File → New Window` or `Ctrl/Cmd + Shift + N`
   - Open the same project folder
   - Command Palette → "Dev Containers: Reopen in Container"
   - Select **"Narev Backend Development"**

Both windows share the same Docker Compose services, giving you:
- ✅ One window with proper TypeScript/React IntelliSense
- ✅ One window with proper Python/Ruff support
- ✅ Both containers running and communicating

```bash
make up    # Starts all services with docker-compose

bashmake up    # Starts all services with docker-compose
```

## Development Environment
### What Each Container Provides
**Frontend Container**:

- ✅ Node.js 22 with pnpm
- ✅ TypeScript/React IntelliSense
- ✅ ESLint and Prettier
- ✅ Vite dev server with hot reload
- ✅ Tailwind CSS support

**Backend Container**:

- ✅ Python 3.12+ with all dependencies
- ✅ Ruff formatting and linting
- ✅ FastAPI with auto-reload
- ✅ PostgreSQL database access
- ✅ Pre-configured VS Code Python extensions



### URLs
- Frontend: http://localhost:5173 (Vite dev server)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Frontend Development Notes
The Vite dev server is configured to bind to `0.0.0.0` for Docker container compatibility. This allows the development server to be accessible from outside the container while maintaining full hot reload functionality.

### File Structure
```
/workspace/
├── .devcontainer/
│   ├── backend/devcontainer.json    # Backend container config
│   ├── frontend/devcontainer.json   # Frontend container config
│   ├── docker-compose.yaml          # Multi-container setup
│   ├── Dockerfile.backend           # Python environment
│   └── Dockerfile.frontend          # Node.js environment
├── .vscode/                         # VS Code settings
├── backend/                         # Python/FastAPI code
├── frontend/                        # Vite React/TypeScript code
└── Makefile                        # Development commands
```

## Development Workflow
### Backend
```bash
# Setup and dependencies
make install-dev       # Install Python dev dependencies

# Code quality (uses Ruff)
make format            # Format code with Ruff
make fix              # Auto-fix linting issues
make lint             # Check linting (no fixes)
make check            # Check formatting + linting (CI-ready)
make format-all       # Format + fix everything

# Testing
make test             # Run pytest
make test-cov         # Run tests with coverage report

# Development
make dev              # Run backend server (uvicorn)
make up               # Start full docker-compose stack
make down             # Stop docker-compose stack

# Cleanup
make clean            # Remove coverage files, cache, etc.
```

### Frontend
### Frontend Development
```bash
# Start the frontend dev server (inside frontend container)
pnpm install          # Install dependencies (first time)
pnpm run dev          # Start Vite dev server with hot reload
pnpm run build        # Build for production
pnpm run preview      # Preview production build locally

# Remove unused dependencies
pnpm remove package-name

# Add new dependencies
pnpm add package-name
pnpm add -D package-name  # Dev dependencies
```

### VS Code Integration
The project includes .vscode/settings.json with:

- ✅ Ruff configured as formatter and linter
- ✅ Python path set correctly for the devcontainer
- ✅ Auto-formatting on save
- ✅ Linting errors shown inline

### Making Changes
1. Edit code - VS Code will auto-format and show linting errors
2. Run the code quality check:
```bash
make format-all   # Format and fix issues
make check        # Verify everything passes
```

3. Test your changes:
```bash
make test         # Run tests
make test-cov     # See coverage report
```

## Code Guidelines
### Python (Backend)

- Formatter: Ruff (automatically applied in VS Code)
- Linter: Ruff (configured in VS Code)
- Style: Modern Python with type hints
- Testing: pytest with good coverage

### Frontend

- Hot reload enabled with Vite
- TypeScript preferred for new code
- ESLint and Prettier configured

### Commit Messages

Use conventional commits:
```
feat: add OpenAI cost breakdown dashboard
fix: resolve FOCUS data validation error
docs: update API documentation
test: add unit tests for billing sync
```

### Pull Request Guidelines
1. Before submitting:
```bash
make format-all    # Format and fix all issues
make check         # Ensure formatting and linting pass
make test-cov      # Run tests with coverage
```
Your PR should:

- ✅ Pass all checks (make check)
- ✅ Include tests for new functionality
- ✅ Update docs if needed
- ✅ Single focus - one feature/fix per PR
- ✅ Clear description of changes

## Troubleshooting
### Devcontainer Issues
```bash
# Rebuild the devcontainer
# In VS Code: Cmd/Ctrl+Shift+P -> "Dev Containers: Rebuild Container"
 
# Or restart the stack
make down
make up
```

### Code Quality Issues
```bash
# Fix most issues automatically
make format-all

# Check what still needs fixing
make check
```
### Questions?
💬 Development questions: GitHub Discussions
🐛 Bug reports: GitHub Issues
📧 General inquiries: opensource@narev.ai


By contributing, you agree to abide by our [Code of Conduct](./CODE_OF_CONDUCT.md).
