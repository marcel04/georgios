# GEO-26 — Cart database schema design

Status: design only. This PostgreSQL schema supports the behavior in
[GEO-25](cart-domain.md). No cart tables, enum, triggers, models, migrations,
API routes, frontend code, seeds, or database changes are implemented here.
Exactly three core tables are proposed: `carts`, `cart_items`, and
`cart_item_modifier_options`.

## Relationships and normalization

```text
carts
  |
  +--< cart_items
          |     |
          |     +--> menu_item_variants --> menu_items
          |
          +--< cart_item_modifier_options
                    |
                    +--> modifier_options --> modifier_groups
```

A cart owns zero or more lines; a line owns zero or more selected-option rows.
Each line references one variant and each selection references one option.
The derivation paths are:

- `cart_item -> menu_item_variant -> menu_item`
- `cart_item_modifier_option -> modifier_option -> modifier_group`

Do not duplicate `menu_item_id` on a cart line or `modifier_group_id` on a
selection. Deriving these values avoids redundant data that could disagree with
the catalog. There is no `cart_item_modifier_groups` table. API requests still
supply grouped selections for validation; storage retains the validated options.
An omitted group and an explicitly empty group both store no selected options.
Required groups must still be checked against the menu, including omitted groups.

## Table definitions

All columns are listed below; no price or display-name columns are persisted.
Defaults marked “none” require the writer to supply a value. UUIDs are generated
by the server; this design does not require a database UUID-generation default.

### `carts`

| Column | PostgreSQL type | Nullability | Default / constraint |
| --- | --- | --- | --- |
| `id` | UUID | NOT NULL | None; PRIMARY KEY |
| `status` | cart_status | NOT NULL | `'ACTIVE'` |
| `expires_at` | TIMESTAMPTZ | NOT NULL | None; server supplies the business deadline |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()`; database update trigger |

The PostgreSQL enum `cart_status` has exactly these values:

| Value | Meaning | Scope |
| --- | --- | --- |
| `ACTIVE` | Cart can be modified while its deadline has not passed | GEO-3 / GEO-25 |
| `EXPIRED` | Inactivity timeout has been reached; cart cannot be revived | GEO-3 / GEO-25 |
| `CONVERTED` | Cart has become an order and is no longer editable | Reserved for the later ordering flow |

GEO-25 defines only ACTIVE/EXPIRED behavior in the current cart API scope.
Reserving `CONVERTED` in the storage enum does not introduce a current conversion
endpoint, transition, or response. Order relationships, conversion transactions,
and HTTP behavior for converted carts remain future ordering design. The enum
limits stored values; it does not itself enforce allowed transitions.

`expires_at` is authoritative, even if a stored status still says ACTIVE after
the deadline. At server time greater than or equal to `expires_at`, a current-scope
cart must be treated as expired on requests without waiting for cleanup. An
existing expired cart returns 410; a missing or eventually deleted cart returns
404. No retention interval or background-job schedule is chosen here.

A new cart is ACTIVE, even when empty, with a deadline ten minutes after server
creation time. Each accepted add, PATCH, or removal sets the deadline to the
server mutation time plus ten minutes. A valid nonempty PATCH assigning existing
values also refreshes it. Reads and rejected requests never refresh it. Removing
the final line leaves an empty ACTIVE cart. `updated_at` records row-update
metadata, not the expiration deadline or a complete history of changes.

### `cart_items`

| Column | PostgreSQL type | Nullability | Default / constraint |
| --- | --- | --- | --- |
| `id` | UUID | NOT NULL | None; PRIMARY KEY |
| `cart_id` | UUID | NOT NULL | None; FK to `carts.id`, ON DELETE CASCADE |
| `menu_item_variant_id` | INTEGER | NOT NULL | None; FK to `menu_item_variants.id`, ON DELETE NO ACTION |
| `quantity` | INTEGER | NOT NULL | None; `CHECK (quantity BETWEEN 1 AND 20)` |
| `special_instructions` | VARCHAR(250) | NULL | Omission stores NULL |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()`; database update trigger |

Every Add to Cart creates a new UUID line, including identical variants and
selections. There is no uniqueness constraint on `(cart_id, menu_item_variant_id)`
or on a configuration. Lines remain independently editable. Zero quantity is
invalid; removal deletes the line. API validation must reject fractional inputs
before database coercion and reject out-of-range quantities.

`VARCHAR(250)` expresses a maximum of 250 characters, not 250 bytes. The API
must validate that bound without silently truncating input. NULL and the empty
string are valid and distinct. Instructions remain plain preparation text and
cannot change prices or replace required selections.

### `cart_item_modifier_options`

| Column | PostgreSQL type | Nullability | Default / constraint |
| --- | --- | --- | --- |
| `cart_item_id` | UUID | NOT NULL | None; FK to `cart_items.id`, ON DELETE CASCADE |
| `modifier_option_id` | INTEGER | NOT NULL | None; FK to `modifier_options.id`, ON DELETE NO ACTION |

`PRIMARY KEY (cart_item_id, modifier_option_id)` prevents the same option from
being selected twice on one line while allowing it on different lines. There
is no separate ID, group ID, quantity, price adjustment, or timestamp on this
join table. Replacing a line's selections replaces its selected-option rows
within the accepted cart mutation transaction.

## Constraints and indexes

| Table / object | Keys and constraints | Indexes |
| --- | --- | --- |
| `cart_status` | Enum: ACTIVE, EXPIRED, CONVERTED | None |
| `carts` | UUID PK; every column NOT NULL; status defaults to ACTIVE | PK index on `id`; B-tree on `(status, expires_at)` |
| `cart_items` | UUID PK; cart FK CASCADE; variant FK NO ACTION; quantity CHECK 1–20; VARCHAR(250); only instructions nullable | PK index on `id`; B-tree on `cart_id`; B-tree on `menu_item_variant_id` |
| `cart_item_modifier_options` | Composite PK; line FK CASCADE; option FK NO ACTION; both columns NOT NULL | PK index on `(cart_item_id, modifier_option_id)`; B-tree on `modifier_option_id` |

Primary keys supply their own unique indexes; do not add duplicate PK indexes.
The join-table PK begins with `cart_item_id`, supporting a line's selection
lookup without another index on that column. Separate indexes on variant and
option references support reference lookups and checks during menu deletion.
The `cart_id` index supports loading a cart's lines and ownership cleanup.

The `(status, expires_at)` index matches equality on status followed by a range
on the deadline, for example this illustrative future query:

```sql
SELECT id
FROM carts
WHERE status = 'ACTIVE'
  AND expires_at <= :server_time;
```

It helps find ACTIVE rows whose deadline has passed without scanning every cart.
It does not refresh deadlines, change status, schedule cleanup, or replace the
request-time expiration check. Indexes cost storage and write maintenance;
these indexes support the expected ownership and expiration access paths.

Database PKs, FKs, nullability, types, and CHECK constraints protect basic
invariants across writers, including direct SQL and concurrent writes.
Application validation additionally supplies useful errors and validates rules
these constraints cannot express: availability, group ownership, group bounds,
variant-specific price support, and request duplicate group/option IDs.
Independent cart variant/option FKs prove existence, not that both belong to the
same item. Existing menu price ownership constraints do not by themselves prove
that a cart selection has a matching price row. The cart service must check it.

## Ownership deletion versus menu deletion

Deleting a cart cascades to its lines, then to their selected-option rows.
Deleting one line cascades only to that line's selections. These rows have no
independent purpose after their owner is gone, so cascades prevent orphan data
and simplify eventual cart cleanup.

Menu references use ON DELETE NO ACTION. Deleting a referenced variant or option
must fail while the cart reference remains, rather than silently removing a
customer's line or selections. Existing menu-side cascades from category, item,
or group deletion can also be blocked when they reach a referenced variant or
option. This applies to retained expired or converted cart rows as well: their
foreign keys continue to exist until their owning data is deleted. Temporary
availability changes can preserve the menu records.

NO ACTION does not detect inactivity, unavailability, changed selection bounds,
or deleted modifier price rows. Those can still make a stored configuration
invalid and must produce GEO-25's `409 cart_menu_conflict` where appropriate.
With these FKs intact, a referenced variant/option cannot simply disappear;
GEO-25's deleted-resource policy does not authorize bypassing the constraints.
The FK deletion error itself is not a cart API 409 response.

For cart requests, retain GEO-25's existence/expiration precedence and validate
the proposed resulting cart. PATCH/DELETE may repair stale selections, but if
any invalid lines remain, reject the whole mutation without changes or deadline
refresh. Never silently delete options or fabricate totals to make a read succeed.

## Current pricing and display data

The cart persists customer intent: variant, selected options, quantity, and
special instructions. It does not persist menu item or variant names, base
variant price, modifier price adjustment, `unit_price`, `line_total`, `subtotal`,
`item_count`, or any other price snapshot.

Every successful cart representation, including mutation responses, resolves
current names and prices through the menu tables. For each selected option,
look up `modifier_option_prices` using both its option ID and the line's variant
ID. A missing row means unsupported selection, never a free choice; a free
choice requires an explicit zero adjustment. Use a consistent view of menu data
for validation and all totals:

```text
unit_price = current variant price + sum(current selected option adjustments)
line_total = unit_price * quantity
subtotal   = sum(line_total)
item_count = sum(quantity)
```

Calculations use decimal arithmetic and responses use two-decimal strings.
An empty cart has no lines, zero item count, and subtotal "0.00". Price-only
changes reprice later reads without refreshing expiration. Selected groups and
options are reconstructed in menu display order, and lines in creation order.

This avoids stale duplicated prices and preserves GEO-25's current-price
contract, at the cost of joins/lookups on reads and explicit stale-menu errors.
Future orders will snapshot agreed historical prices for receipts and audit;
reserving CONVERTED does not make a cart an order-price snapshot.

## UUIDs and access boundaries

Use server-generated unpredictable UUIDs for `carts.id` and `cart_items.id` so
public/guest resource identifiers are opaque and non-sequential. UUIDs take more
space than integer identifiers and do not supply chronological ordering. Menu
and catalog IDs remain INTEGER, matching the existing models.

The guest cart UUID is an access credential, not customer identity. UUIDs do
not replace ownership validation: always scope line lookup by both cart ID and
line ID. Keep cart IDs out of analytics/logs and use HTTPS as GEO-25 requires.

## Timestamp conventions and implementation boundaries

Follow the existing [menu models](../../backend/app/models/menu.py) and
[initial menu migration](../../backend/alembic/versions/361f81bb87ba_create_menu_tables.py):
TIMESTAMPTZ (`DateTime(timezone=True)`), `now()` defaults for creation/update
metadata, and a BEFORE UPDATE trigger using the existing `set_updated_at()`
convention. That function assigns `CURRENT_TIMESTAMP`; cart triggers are only
proposed here. Preserve `created_at` on updates. API timestamps remain UTC ISO
8601 strings.

Triggers affect only their own row; child changes do not automatically update
parents. Future accepted mutations must explicitly update the cart's deadline
in the same transaction as line/selection changes. `expires_at` has no generic
update trigger: audit updates, reads, or marking expiration must not extend it.
PostgreSQL's transaction timestamp used for audit metadata must not be mistaken
for a fresh expiration-check time after waiting on a lock.

The expiration check, accepted mutation, and deadline refresh must be atomic;
locking/isolation and menu-read consistency mechanisms remain implementation
work. No time-dependent CHECK constraint or index substitutes for these rules.

Open implementation details remain:

- Choose server UUID generation and the transaction/locking strategy, including
  obtaining the authoritative mutation time after any lock wait.
- Query line creation order explicitly. Timestamp ties need an agreed ordering
  policy; UUID order is not insertion order. The agreed fields do not encode a
  separate sequence for strict ordering among equal timestamps.
- Define cleanup retention and later conversion/order behavior. GEO-3 continues
  to expose only ACTIVE/EXPIRED behavior; no converted-cart HTTP contract is
  invented here.

## GEO-25 consistency review

The design preserves separate adds, 1–20 quantities, nullable 250-character
instructions, grouped request validation, current decimal pricing, and all four
derived totals. It preserves mutation-only ten-minute expiration, the exact
deadline boundary, empty active carts, 404/410 distinctions, and atomic rejection
and stale-menu repair rules. The only lifecycle extension is a reserved database
enum value for future ordering, outside current API behavior. Normalized storage
still allows display-ready responses with derived IDs and current menu names.
All database enforcement and runtime verification remain future work.
