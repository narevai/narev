# Contributing

We want you here. Especially if youre not a bot.

## Ways to Contribute

- **Report bugs** via [GitHub Issues](https://github.com/narevai/varne/issues)
- **Suggest features** for better AI cost tracking
- **Improve documentation** 
- **Submit code changes**
- **Add test coverage**

### Before You Start

1. Check existing [issues](https://github.com/narevai/varne/issues) and [PRs](https://github.com/narevai/varne/pulls)
2. Read our [Code of Conduct](CODE_OF_CONDUCT.md)
3. For large changes, open an issue first to discuss

### Contribution Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** (see Development Setup below)
4. **Test your changes** using the `make` commands in `backend/` (see below)
5. **Submit a pull request**

## Development Environment Setup

### Prerequisites

- **VS Code** or **Cursor** with the **Dev Containers** extension
- **Docker Desktop** running
- Git access to the repository

### Setup

1. Clone the repository

```bash
git clone https://github.com/narevai/varne.git
cd varne
```

1. **Reopen in the dev container**
   - When prompted, choose **Reopen in Container**, or
   - Command Palette (Cmd/Ctrl+Shift+P): **Dev Containers: Reopen in Container**
   - This project uses a single **varne Development** configuration (see `.devcontainer/devcontainer.json`), backed by `.devcontainer/docker-compose.yaml`.

2. **Environment file**
   - Copy `.env.example` to `.env` if you do not have one yet.
   - For local full-stack development, set **`VITE_API_URL=http://localhost:8000`** in `.env` (see `.env.example`). The frontend uses this in dev so API calls go to the FastAPI server; without it, the client defaults to same-origin and API requests from the Vite dev server usually fail.

3. **Dependencies (first time or after lockfile changes)**

   - The devcontainer **post-create** step runs `make install` in `backend/` (system Python, no venv). If that did not run or failed, install manually:

```bash
cd /workspace/backend && make install
```

   - For frontend work, install Node dependencies separately:

```bash
pnpm install --dir /workspace/frontend
pnpm install --dir /workspace/docs
```

## Development Environment

### What the dev container provides

One **dev** service includes:

- ✅ Python 3.12 with **uv**; backend dependencies installed on container create via `make install` (system Python)
- ✅ Workspace mounted at `/workspace`
- ✅ Ports forwarded for Vite and the API (see `devcontainer.json`)

### URLs

- Frontend: http://localhost:5173 (Vite dev server; start with `pnpm run dev` in `frontend/`)
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Running backend and frontend

Use **two terminals** inside the dev container (start the app processes yourself).

**Backend** (from `backend/`):

```bash
cd /workspace/backend
make dev
```

This runs FastAPI with uvicorn and reload on port 8000. Default local database is **SQLite** under `backend/data` unless you change settings.

**Frontend** (from `frontend/`):

```bash
cd /workspace/frontend
pnpm run dev
```

### Quick smoke test (everything wired for developers)

| Check | What to do |
|--------|------------|
| Python | `python -c "import fastapi; print('ok')"` |
| Backend | `cd /workspace/backend && make dev`, then open `/health` and `/docs` |
| Frontend | `cd /workspace/frontend && pnpm run dev`, open port 5173 |
| Full stack | Backend + frontend running, `VITE_API_URL` set → confirm browser network calls hit `http://localhost:8000` |

### Devcontainer lifecycle

To rebuild or restart the dev container, use the editor: Command Palette → **Dev Containers: Rebuild Container**. To control the Compose project from the host:

```bash
docker compose -f .devcontainer/docker-compose.yaml up -d --build
docker compose -f .devcontainer/docker-compose.yaml down
```

When you are already **inside** the rebuilt dev container, the **dev** service is usually already running; you still start **uvicorn** and **Vite** with the commands above.

### Frontend development notes

The Vite dev server is configured to bind to `0.0.0.0` for Docker compatibility so you can open it from the host while hot reload keeps working.

### File structure

```
/workspace/
├── .devcontainer/
│   ├── devcontainer.json      # Dev container definition
│   ├── docker-compose.yaml    # dev service + uv cache volume
│   └── Dockerfile.dev         # Python + uv base image
├── .vscode/                   # Editor settings
├── backend/                   # Python/FastAPI code (includes Makefile)
├── frontend/                  # Vite React/TypeScript code
└── docs/                      # Documentation site
```

## Development Workflow

Run **`make`** targets from **`/workspace/backend`** (the backend `Makefile` lives there).

### Backend

```bash
cd /workspace/backend

make install   # Install Python dev dependencies (first time or after lockfile changes)
make format    # Format code and auto-fix lint issues
make check     # Verify formatting and linting (same as CI)
make test      # Run pytest
make dev       # Run backend server (uvicorn on port 8000)
```

**Extra commands** (not in the Makefile):

```bash
uv run pytest --cov=. --cov-report=term-missing   # Tests with coverage
uv tool run deptry .                              # Audit unused/missing dependencies
rm -rf htmlcov .coverage .pytest_cache            # Clean test artifacts
uv run python tests/mock_api/server.py            # Mock API for integration tests
```

### Frontend

```bash
cd /workspace/frontend

pnpm install           # Install dependencies (first time or after clone)
pnpm run dev           # Start Vite dev server with hot reload
pnpm run build         # Build for production
pnpm run preview       # Preview production build locally

# Remove unused dependencies
pnpm remove package-name

# Add new dependencies
pnpm add package-name
pnpm add -D package-name   # Dev dependencies
```

### VS Code Integration

The project includes .vscode/settings.json with:

- ✅ Ruff configured as formatter and linter
- ✅ Python interpreter: `/usr/local/bin/python` (system Python, no venv)
- ✅ Auto-formatting on save
- ✅ Linting errors shown inline

### Making Changes

1. Edit code — the editor will auto-format and show linting errors where configured.
2. Run the code quality check (from `backend/`):

```bash
cd /workspace/backend
make format   # Format and fix issues
make check    # Verify everything passes
```

1. Test your changes:

```bash
make test
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
1. Before submitting (from `backend/`):
```bash
cd /workspace/backend
make format    # Format and fix all issues
make check     # Ensure formatting and linting pass
make test      # Run tests
```
Your PR should:

- ✅ Pass all checks (make check)
- ✅ Include tests for new functionality
- ✅ Update docs if needed
- ✅ Single focus - one feature/fix per PR
- ✅ Clear description of changes

## Troubleshooting
### Devcontainer issues

- Rebuild: Command Palette → **Dev Containers: Rebuild Container**.

Restart the Compose stack:

```bash
docker compose -f .devcontainer/docker-compose.yaml down
docker compose -f .devcontainer/docker-compose.yaml up -d --build
```

### Code quality issues

```bash
cd /workspace/backend
make format    # Fix most issues automatically
make check     # See what still needs fixing
```

By contributing, you agree to abide by our [Code of Conduct](./CODE_OF_CONDUCT.md).
