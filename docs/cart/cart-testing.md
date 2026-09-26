# Cart backend testing — GEO-34

The audit covers the implemented GEO-25 guest-cart contract: create/read,
configured adds, quantity-only PATCH, and single-line DELETE. Configuration
editing, checkout, cleanup, and frontend behavior are not implemented or verified.

## Coverage map

| Test file (`backend/tests/`) | Verified behavior |
| --- | --- |
| `test_carts.py` | PostgreSQL UUID/defaults, enum, constraints, ownership cascades, protected menu references, timestamp triggers |
| `test_cart_api.py` | Creation/Location, empty representation, retrieval, ten-minute deadline, unchanged reads, exact expiration boundary, persisted EXPIRED status, 404/410/422, current pricing and conflicts |
| `test_cart_add.py` | Required/optional selections, ownership, duplicates, availability, explicit zero versus missing prices, strict quantity/instructions, separate lines, rollback, PostgreSQL locking |
| `test_cart_quantity.py` | Quantity bounds/no-op refresh, preserved configuration, independent lines, scoped ownership, repricing and stale-state rollback |
| `test_cart_remove.py` | Cascade cleanup, retained empty ACTIVE cart, repeated-delete 404, stale-target recovery and rollback when other stale lines remain |
| `test_cart_pricing.py` | Exact Decimal unit/line/subtotals, quantity counts, multiple variants/adjustments, all endpoints, repricing without persisted-intent changes, tampering, one-SELECT GET |
| `test_cart_stale.py` | All affected lines reported, changed min/max and omitted newly required groups, availability, unsupported prices, 422 new requests versus 409 stored state, regrouping/ownership, full-row rollback checks |
| `test_cart_workflow.py` | Two independently configured menu items through add/GET/PATCH/DELETE to empty cart; stale modifier recovery while retaining another valid configured line |

Existing tests already covered most requested lifecycle, arithmetic, security,
and error semantics. GEO-34 adds the two-item workflow/recovery scenarios,
PATCH expiration-after-lock coverage, unrelated-cart progress under a held lock,
and a stale expiration read after a committed refresh. It preserves rather than
repeats existing separate-add, missing-price, no-refresh and rollback tests.

## Running tests

From `backend/`, the default suite uses isolated SQLite API fixtures and skips
PostgreSQL-specific cases:

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

For PostgreSQL, start the repository's local service (`docker compose up -d` from
repository root), configure `backend/.env` as described by its example, and use
a development database with migrations applied. Then run from `backend/`:

```sh
uv run alembic current
uv run alembic check
GEO27_DB_TESTS=1 uv run pytest tests/test_cart*.py --tb=short
```

The established `GEO27_DB_TESTS` flag enables both API database variants and the
PostgreSQL model/concurrency tests. It does not enable unrelated GEO20 integration
tests. `DATABASE_URL` explicitly provided by the environment takes precedence;
use the configured development PostgreSQL URL for this opt-in run.

From repository root, also run `git diff --check`.

## Fixtures and database isolation

`conftest.py` supplies SQLite with foreign keys enabled and a shared in-memory
connection for TestClient. The cart fixture in `test_cart_api.py` emulates only
the PostgreSQL UUID default on SQLite. It overrides the database dependency and
restores overrides in `finally`. PostgreSQL cases no longer construct an unused
SQLite engine; the SQLite fixture is requested only for SQLite cases.

API integration cases use an outer connection transaction plus request-session
savepoints. Request commits can therefore be exercised while test data rolls
back at teardown. SQLite databases are discarded after each case; SQLite's
transaction/UUID behavior is not evidence of PostgreSQL semantics. Configured
menu fixtures use generated database IDs rather than production seed IDs.

Existing test-module fixture imports are retained to avoid a broad unrelated
reorganization. Concurrency tests require independent connections, commit their
own temporary fixtures, and delete their owned rows in `finally`. Run against a
development database, not production. This suite is not verified with pytest-xdist
or concurrent independent runs: category display-order allocation uses max+1,
and API dependency overrides are process-global.

## Concurrency and consistency

Real PostgreSQL tests cover simultaneous adds, quantity updates, and removal plus
update on one cart. A held parent lock and observed PostgreSQL lock wait establish
that add/PATCH/DELETE sample expiration time after lock acquisition and reject an
expired cart. Another test holds one cart lock while a different cart completes
the shared mutation transaction. This checks lock granularity, not throughput.

A deterministic two-transaction interleaving loads an old deadline, commits a
refresh, then invokes the old reader's expiration check. The refreshed cart must
remain ACTIVE with the committed deadline. This directly exercises the race
condition without relying on thread timing.

GET pricing/validation eagerly loads a single statement snapshot. Tests count one
SELECT for one and six configured lines on both engines; no N+1 regression was
observed. Joined collections can still multiply returned rows. These tests do not
establish latency, throughput, production capacity, or all possible concurrent
menu-administration schedules.

## Limits and results

The normalized schema derives current option/group ownership; original group
assignments and historical order prices are not stored. Foreign keys are not
weakened to simulate deleted referenced menu data. Price-row deletion and menu
availability/rule changes provide valid stale-state scenarios. Quantity-only
PATCH cannot repair modifier selections; DELETE can repair only when the resulting
cart is valid. No production defect was found during this audit.

Verification on 2026-09-26:

- Default suite: **158 passed, 139 skipped** (297 collected).
- PostgreSQL-enabled cart suite: **245 passed, 0 skipped**.
- Ruff lint and format checks passed (37 Python files formatted).
- Alembic: `c7a27f31d902` at head; no schema drift.
- `git diff --check` passed.
- Each test run reports one existing Starlette/AnyIO `BlockingPortal`
  deprecation warning. No blocker or production-code change was required.
