# Contributing

## Project structure

- `frontend/`: Next.js and TypeScript application.
- `backend/`: FastAPI and Python application.
- `docs/`: Project documentation, including the engineering journal.
- `.github/workflows/`: GitHub Actions quality checks.

The frontend currently displays a placeholder page, and the backend exposes `GET /health`. Database, payment, authentication, and deployment features are not implemented.

## Prerequisites

- Git and access to the GitHub repository.
- Node.js 24 with npm, matching `frontend/.nvmrc` and CI.
- Python 3.12 to match CI; `backend/pyproject.toml` supports Python 3.9 or newer.
- uv installed and available on your terminal's `PATH`; see the installation link in the [backend setup instructions](README.md#run-the-backend).
- VS Code is a recommended editor, not a requirement.

## Clone and setup

With GitHub SSH access configured:

```bash
git clone git@github.com:marcel04/georgios.git
cd georgios
```

The following frontend and backend setup blocks each start from this repository root. Use separate terminals for the two development servers. Stop either server with Ctrl+C.

### Frontend

Install dependencies and start the frontend:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. In another terminal, from `frontend/`, run quality checks:

```bash
npm run lint
npm run typecheck
npm run build
```

These run ESLint, TypeScript checking without emitting compiled files, and a production build. If a restricted environment blocks Turbopack's worker ports, use the documented fallback `npm run build -- --webpack` and mention that limitation in your PR. CI uses the standard build command.

### Backend

Install dependencies and start the backend:

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

uv manages `.venv` and installs runtime and default development dependencies using `pyproject.toml` and `uv.lock`; manual activation is unnecessary. Keep both dependency files in version control.

Open http://localhost:8000/health to check for `{"status":"ok"}`. In another terminal, from `backend/`, run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

These check Python lint rules, formatting, and tests. The health test runs in-process without a running server. CI uses `uv sync --locked` and enforces locked mode for subsequent commands.

## Environment variables

When local environment files are needed, copy the templates from the repository root. Skip a copy if you already have that local file so you preserve your settings:

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

The templates contain only `NEXT_PUBLIC_API_URL=http://localhost:8000` for the frontend and `FRONTEND_URL=http://localhost:3000` for the backend. Neither application currently uses these values; the backend does not automatically load `.env` files. They are not required to run the current applications.

Real `.env` files and local variants must never be committed; Git ignores them. Tracked `.env.example` files must contain safe templates only. `NEXT_PUBLIC_` variables are public frontend configuration and must not contain secrets.

## Ticket to merge

Jira status flow:

```text
Backlog -> Ready -> In Progress -> Code Review -> Testing -> Done
```

Use **Backlog** for work not yet ready to start. The separate **Testing** stage applies when additional testing is needed after review, as established in GEO-13.

```text
Jira ticket -> Ready -> developer starts work -> In Progress
-> feature/bugfix/chore branch -> implementation -> pull request
-> Code Review -> CI/testing -> merge -> Done
```

1. Confirm the Jira ticket is **Ready** before implementation begins. Move it to **In Progress** when you start work.
2. Create a branch from up-to-date `main` using the naming conventions below. Implement the ticket and run the relevant [frontend](README.md#frontend-quality-checks) and [backend](README.md#backend-quality-checks) checks locally.
3. Open a pull request targeting `main`. When it is ready for review, move the ticket to **Code Review**.
4. Address review feedback and verify CI passes. If separate testing is needed after review, move the ticket to **Testing** and record the results in the PR.
5. Merge after review comments are resolved and CI/testing passes. Move the ticket to **Done** only after the change is merged and accepted against its acceptance criteria.

These are contributor conventions, not a claim that Jira transitions or GitHub branch protections are configured.

## Branches and commits

| Work | Branch pattern | Example |
| --- | --- | --- |
| Feature | `feature/GEO-<ticket>-short-description` | `feature/GEO-21-menu-categories` |
| Bug fix | `bugfix/GEO-<ticket>-short-description` | `bugfix/GEO-35-cart-total` |
| Maintenance or setup | `chore/GEO-<ticket>-short-description` | `chore/GEO-13-collaboration-workflow` |

Prefer concise commit messages that reference the Jira ticket:

```text
GEO-21 add menu category endpoint
GEO-35 fix cart total calculation
```

## Pull requests and review

- Reference the Jira ticket and explain what changed.
- Include testing performed and results, including relevant manual checks or any verification limitations.
- Keep each PR focused on one ticket when practical. Do not mix unrelated changes.
- Once multiple developers are active, obtain review from at least one other contributor. Authors should not approve their own PRs. While working solo, still use PRs, inspect the diff, and require passing CI.
- Review for correctness, maintainability, tests, security, and scope. Resolve review comments before merging.

The existing [CI workflow](.github/workflows/ci.yml) runs on PRs targeting `main` and pushes to `main`. Its frontend job runs lint, TypeScript checks, and the production build; its backend job runs Ruff lint, formatting checks, and pytest. Both jobs should pass on the latest PR changes before merge. CI may run while review is in progress; it does not replace review or ticket-specific testing.

## Main and merging

Changes should reach `main` through pull requests; contributors should not normally push directly to `main`.

Prefer **squash merging** normal feature and bug-fix PRs so each Jira ticket has a clean commit on `main`. Use a concise squash commit message referencing the ticket. Preserve meaningful commit history only when there is a clear reason, explained in the PR.

## Secrets and security

Never commit API keys, passwords, tokens, real credentials, or real `.env` files. Review your diff before committing. If a secret is accidentally committed, notify the team immediately so it can be revoked or rotated; deleting it only in a later commit does not remove it from Git history.

## Project journal

Meaningful completed work, architecture decisions, debugging stories, and lessons may be added to `docs/project-journal.md`. Record actual changes and verification results, and distinguish local verification from merged or deployed work. Keep plans explicitly labeled as plans; never claim planned work is implemented.
