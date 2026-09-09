# Georgios

An online-ordering platform for a restaurant, starting with a minimal application foundation.

Unofficial portfolio project. This project is not affiliated with or endorsed by Georgio's Roast Beef & Pizza.

## Architecture

This monorepo contains two separate applications, each with its own dependencies and development server:

```text
frontend/           Next.js, TypeScript, App Router, Tailwind CSS, ESLint
  app/              Root layout, styles, and placeholder home page
backend/            Python FastAPI application
  app/main.py       Application and health endpoint
  pyproject.toml    Backend dependencies and quality-check configuration
  uv.lock           Locked backend dependency versions
```

The frontend currently displays a placeholder page. The backend exposes only `GET /health`, returning `{"status":"ok"}`. Automatic API documentation and OpenAPI routes are disabled. There is no database, authentication, payment integration, or restaurant business logic yet.

## Local environment files

From the repository root, copy the templates to create local environment files:

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

The frontend template sets `NEXT_PUBLIC_API_URL=http://localhost:8000`, and the backend template sets `FRONTEND_URL=http://localhost:3000`.

These values prepare configuration for future frontend/backend integration; neither application currently uses them. The backend does not currently load `.env` files automatically.

Real `.env` files and their local variants are ignored by Git. The `.env.example` templates are version-controlled and must contain only safe placeholder values, never secrets or credentials. Variables prefixed with `NEXT_PUBLIC_` are public frontend configuration and must never contain secrets.

## Run the frontend

Prerequisite: Node.js 24 LTS (with npm).

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. Dependencies are locked in `frontend/package-lock.json`.

To serve a production build, run `npm run build` followed by `npm start`.

### Frontend quality checks

From the repository root:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

These run ESLint, generate Next.js route types and check TypeScript without emitting compiled files, and verify the production build.

If a restricted environment blocks Turbopack's local worker ports, build with
`npm run build -- --webpack` instead.

## Run the backend

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.9 or newer. Run in a separate terminal from the repository root:

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

`uv sync` manages `backend/.venv` and installs runtime and development dependencies from `pyproject.toml` using `uv.lock`. No manual virtual-environment activation is needed, including on Windows. The development server reloads when Python files change.

Keep `pyproject.toml` and `uv.lock` in version control. Use `uv add <package>` for runtime dependencies or `uv add --dev <package>` for development tools; these commands update the manifest and lockfile together. Use `uv sync --locked` to verify installation without changing the lockfile.

Check the running service:

```bash
curl http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok"}`.

Neither application requires environment variables for this initial setup. Virtual environments are also ignored by Git.

### Backend quality checks

From the repository root:

```bash
cd backend
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

`pyproject.toml` declares FastAPI and Uvicorn as runtime dependencies. Its `dev` dependency group includes the FastAPI CLI, Ruff, pytest, and HTTPX for FastAPI's test client. Ruff checks lint rules and formatting using the same file. To apply formatting fixes, run `uv run ruff format .`.

The pytest health test checks that `GET /health` returns HTTP 200 and `{"status":"ok"}`. It runs in-process and does not require a running backend server.
