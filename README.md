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
  requirements.txt  Backend dependencies
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

To check and build the frontend:

```bash
npm run lint
npm run typecheck
npm run build
npm start
```

`npm start` serves the production build after `npm run build`.

If a restricted environment blocks Turbopack's local worker ports, build with
`npm run build -- --webpack` instead.

## Run the backend

Prerequisite: Python 3.9 or newer. Run in a separate terminal from the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

On Windows, activate the environment with `.venv/Scripts/Activate.ps1` in PowerShell.

Check the running service:

```bash
curl http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok"}`.

Neither application requires environment variables for this initial setup. Virtual environments are also ignored by Git.
