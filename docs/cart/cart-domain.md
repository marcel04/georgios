# GEO-25 — Cart domain rules and initial API contract

Status: design only. This document defines the GEO-3 cart behavior; it does not
implement it. PostgreSQL cart schema design belongs to GEO-26. Models, migrations,
FastAPI routes, frontend changes, checkout, tax, tips, payment fees, and grand-total
calculations are outside this ticket.

## Storage and guest access

Carts are persisted in PostgreSQL and work without customer authentication. The
server generates an unpredictable UUID for each cart. The frontend retains that
UUID and supplies it in subsequent cart URLs. Browser storage mechanics are a
frontend implementation decision.

Persistence keeps cart state on the server across requests and application
restarts, at the cost of database reads/writes and eventual cleanup. The UUID is
a guest access credential: possession allows access to that cart, not proof of
customer identity. Use HTTPS and avoid exposing cart IDs in analytics or logs.
Losing the UUID means creating a new cart; account recovery/merging is not defined.

## Lifecycle and inactivity

The only states are `ACTIVE` and `EXPIRED`. A new cart is `ACTIVE`, including when
empty, with `expires_at` set to server creation time plus 10 minutes. Timestamps
in responses are UTC ISO 8601 strings.

- A successful add, update, or removal sets `expires_at` to the server mutation
  time plus 10 minutes. Removing the last line leaves an empty active cart.
- GET/read operations never refresh expiration. Polling cannot keep a cart alive.
- Failed validation, missing resources, and rejected mutations do not refresh it.
- At server time **greater than or equal to** `expires_at`, the cart is expired.
  Expiration is checked on requests, regardless of whether cleanup has run.
- A missing cart returns `404 Not Found`; an existing expired cart returns
  `410 Gone` for GET and all item mutations. An expired cart cannot be revived;
  the frontend creates a new cart.
- No converted, checked-out, or other lifecycle states exist in this scope.

Implementation must make the expiration check, accepted mutation, and timer
refresh atomic so concurrent operations cannot revive an expired cart or lose
an accepted update. Transaction/locking mechanisms and physical cleanup are
future implementation work. Cleanup must preserve the documented distinction:
a retained expired cart returns 410; after eventual deletion it is missing (404).
No retention duration is chosen here.

Example: created at 12:00 → expires at 12:10; GET at 12:05 leaves 12:10 unchanged;
accepted add at 12:08 → expires at 12:18; a request at 12:18 returns 410.

## Cart lines and instructions

Every Add to Cart action creates a **new line**, even for identical variants and
modifiers. Each line has its own server-assigned ID, quantity, instructions, and
selections. Separate lines preserve customer intent (for example two meals that
may later receive different instructions) and allow independent editing. The
tradeoff is more rows and potentially repetitive UI; automatic merging would
need configuration equality and would obscure that independence. Repeating a
POST can create another line; retry deduplication is not promised by this contract.

Quantity is an integer from **1 through 20 inclusive per line**. Zero, negative,
fractional, and greater-than-20 quantities are invalid. Removal uses DELETE.
Optional `special_instructions` accepts a string of at most **250 Unicode
characters** or null. Omission on creation means null; an empty string is allowed.
Instructions are plain text for preparation, never a source of price changes or
a substitute for required modifier selections. Render them as text, not HTML.

## Grouped modifier selections and validation

Creation requests identify the variant and group options explicitly:

```json
{
  "menu_item_variant_id": 88,
  "quantity": 1,
  "special_instructions": "Well done",
  "modifier_groups": [
    { "modifier_group_id": 20, "option_ids": [201] },
    { "modifier_group_id": 21, "option_ids": [207] }
  ]
}
```

The backend derives the menu item from the variant. Grouping makes the request
match the menu's configuration rules and permits useful group-specific errors;
client grouping is not evidence that a selection is legitimate. Validate:

1. The variant and its menu item exist and are available, and the parent category
   is active.
2. Every supplied group belongs to that menu item and is active.
3. Every option belongs to its supplied group and is available.
4. Every active group's min/max selection bounds are satisfied, including groups
   omitted from the request. An omitted group has zero selections; a required
   group (`min_selections > 0`) cannot be bypassed by omission.
5. Each selected option has a `ModifierOptionPrice` row for the chosen variant.
   A missing row means unsupported selection, **not a free option**. A free
   choice requires an explicit `"0.00"` adjustment.
6. Group IDs are unique in the request and option IDs are unique within each
   group; duplicates are rejected rather than counted toward selection limits.

`modifier_groups` defaults to `[]` on creation; omitting it is valid only when
all required selections are satisfied. Each supplied group requires `option_ids`;
an empty list represents zero selections. Options have no separate quantity.

## Pricing and totals

The backend is authoritative. Clients send identifiers, quantities, instructions,
and selections; they cannot set prices, totals, status, or expiration. Reject
unknown request fields, including price fields. Revalidate against menu data even
when the request came from the official frontend: browser requests can be altered.
Otherwise an attacker could submit a cheaper price or combine unrelated options.

Resolve **current** variant prices and applicable modifier adjustments whenever
producing a cart representation. Do not snapshot historical prices in a cart.
Use decimal arithmetic and return monetary amounts as decimal strings with two
fractional digits, consistent with the current menu's two-decimal monetary data.
Never use binary floating-point numbers for monetary calculations or responses.

```text
unit_price = current variant base price + sum(selected modifier adjustments)
line_total = unit_price * quantity
subtotal   = sum(line_total for all cart lines)
item_count = sum(quantity for all cart lines)
```

A selected modifier adjustment is per unit, so quantity multiplies the complete
configured unit price. Empty carts have `subtotal: "0.00"`, `item_count: 0`, and
`items: []`. Item count is not the number of rows. All totals in a response must
be derived from a consistent view of current menu data.

A cart is editable purchase intent, not a price guarantee. A menu price change
can change a later GET subtotal without refreshing expiration. Future orders
must snapshot agreed prices to preserve the transaction's historical amount
for receipts and audit even after the menu changes; checkout revalidation and
order snapshots are deferred to the ordering system.

## Initial HTTP contract

The following completes the supplied domain decisions with initial contract
choices: full-cart mutation responses, PATCH replacement rules, error codes,
and stale-menu handling. These are design choices for implementation, not
existing endpoint behavior. Example IDs and menu names are illustrative fixtures.
Menu IDs are integers; cart IDs are UUID strings. Cart-item IDs are opaque
server-assigned strings (UUIDs in examples); their storage is deferred to GEO-26.

| Method and path | Request body | Success |
| --- | --- | --- |
| `POST /api/carts` | No body (empty object also accepted) | 201, full empty cart; `Location: /api/carts/{cart_id}` |
| `GET /api/carts/{cart_id}` | None | 200, full current cart |
| `POST /api/carts/{cart_id}/items` | Variant, quantity, optional instructions and grouped selections | 201, full updated cart |
| `PATCH /api/carts/{cart_id}/items/{cart_item_id}` | At least one editable field | 200, full updated cart |
| `DELETE /api/carts/{cart_id}/items/{cart_item_id}` | None | 200, full updated cart |

Successful responses share the display-ready shape below. The frontend needs no
additional menu lookup to render a valid cart. Lines are returned in creation
order; selected groups/options follow menu display order. Names are current menu
names. Read-only `unit_price` and `line_total` are line fields; `subtotal` and
`item_count` are cart fields. Every successful response includes `expires_at`.

### Create a cart

`POST /api/carts` at 12:00 returns 201:

```json
{
  "id": "38e2fe45-fb96-4a24-b5d7-3a1de09ec56d",
  "status": "ACTIVE",
  "expires_at": "2026-09-19T12:10:00Z",
  "item_count": 0,
  "subtotal": "0.00",
  "items": []
}
```

### Add an item and read the cart

POST the grouped request above to
`/api/carts/38e2fe45-fb96-4a24-b5d7-3a1de09ec56d/items` at 12:08.
With an illustrative base price of `"10.00"`, the 201 response is:

```json
{
  "id": "38e2fe45-fb96-4a24-b5d7-3a1de09ec56d",
  "status": "ACTIVE",
  "expires_at": "2026-09-19T12:18:00Z",
  "item_count": 1,
  "subtotal": "12.50",
  "items": [
    {
      "id": "40a32e59-a166-44ac-a6d7-90d322b87068",
      "menu_item_id": 42,
      "menu_item_name": "Roast Beef Sandwich",
      "menu_item_variant_id": 88,
      "menu_item_variant_name": "Regular",
      "quantity": 1,
      "special_instructions": "Well done",
      "modifier_groups": [
        {
          "modifier_group_id": 20,
          "modifier_group_name": "Bread",
          "options": [
            { "modifier_option_id": 201, "modifier_option_name": "Gluten Free Roll", "price_adjustment": "2.50" }
          ]
        },
        {
          "modifier_group_id": 21,
          "modifier_group_name": "Sauce",
          "options": [
            { "modifier_option_id": 207, "modifier_option_name": "BBQ", "price_adjustment": "0.00" }
          ]
        }
      ],
      "unit_price": "12.50",
      "line_total": "12.50"
    }
  ]
}
```

GET `/api/carts/38e2fe45-fb96-4a24-b5d7-3a1de09ec56d` at 12:09 returns
200 with this same body if the menu is unchanged, including the unchanged
12:18 expiry. Adding the same configuration again yields a different line ID,
two rows, `item_count: 2`, and `subtotal: "25.00"`.

### Update an item

PATCH the item URL ending in `/items/40a32e59-a166-44ac-a6d7-90d322b87068`:

```json
{
  "quantity": 2,
  "special_instructions": null
}
```

Accepted at 12:11, this returns 200 with the full single-line cart above, except
`quantity` and `item_count` are 2, `special_instructions` is null,
`line_total` and `subtotal` are `"25.00"`, and `expires_at` is
`"2026-09-19T12:21:00Z"`. Unit price stays `"12.50"` if menu prices are unchanged.

PATCH accepts `quantity`, `special_instructions`, `menu_item_variant_id`, and
`modifier_groups`. Omitted fields retain their values. Supplied modifier groups
**replace the complete selection**, rather than merging individual groups;
`[]` clears all selections only if current rules allow it. Only instructions
accept null. Validate the resulting entire line, including retained selections
against a changed variant. The line ID remains unchanged. Reject an empty PATCH;
a valid nonempty PATCH assigning the same values counts as an accepted update
and refreshes expiration. No partial changes are saved on failure.

### Remove an item

DELETE the same item URL at 12:12 returns 200 (not 204), with an empty cart:

```json
{
  "id": "38e2fe45-fb96-4a24-b5d7-3a1de09ec56d",
  "status": "ACTIVE",
  "expires_at": "2026-09-19T12:22:00Z",
  "item_count": 0,
  "subtotal": "0.00",
  "items": []
}
```

Deleting an already removed line returns 404 without a timer refresh.

## Errors and menu changes

| Condition | HTTP status | Error code |
| --- | --- | --- |
| Cart does not exist | 404 | `cart_not_found` |
| Cart exists but has expired | 410 | `cart_expired` |
| Line does not belong to the specified active cart, or is missing | 404 | `cart_item_not_found` |
| Invalid body/path types, quantity, instructions, unknown fields, or selections | 422 | `validation_error` |
| Stored configuration is no longer valid against the menu | 409 | `cart_menu_conflict` |

For structurally valid requests, check cart existence and expiration before line
lookup or menu validation. Scope line lookup to its parent cart. Malformed UUIDs
are validation errors, not missing-cart lookups. Error responses use this shape
(`details` is an array; empty when no field/line information is needed):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Quantity must be between 1 and 20.",
    "details": [{ "field": "quantity", "reason": "out_of_range" }]
  }
}
```

An expired cart returns 410 with its deadline:

```json
{
  "error": {
    "code": "cart_expired",
    "message": "This cart has expired. Create a new cart.",
    "details": []
  },
  "cart_id": "38e2fe45-fb96-4a24-b5d7-3a1de09ec56d",
  "status": "EXPIRED",
  "expires_at": "2026-09-19T12:22:00Z"
}
```

Current pricing also requires a defined policy for disappearing menu data. This
initial contract chooses 409 when existing lines reference unavailable/deleted
items, variants, groups, options, missing price rows, or no longer satisfy current
selection bounds. A price-only change simply reprices the cart. Never silently
remove selections, substitute free prices, or return fabricated totals.

```json
{
  "error": {
    "code": "cart_menu_conflict",
    "message": "A cart selection is no longer available.",
    "details": [
      {
        "cart_item_id": "40a32e59-a166-44ac-a6d7-90d322b87068",
        "field": "modifier_groups",
        "modifier_group_id": 20,
        "modifier_option_id": 201,
        "reason": "option_unavailable"
      }
    ]
  },
  "cart_id": "38e2fe45-fb96-4a24-b5d7-3a1de09ec56d",
  "status": "ACTIVE",
  "expires_at": "2026-09-19T12:18:00Z"
}
```

Conflict details identify all affected lines and relevant known selection IDs so
the frontend can request reconfiguration or removal. Menu lookup may be needed
for reconfiguration, but not for rendering a successful cart response. Rejected
requests save nothing and do not refresh expiration. PATCH/DELETE can repair a
stale cart: validate the proposed resulting cart, allowing removal of an invalid
line or replacement of invalid selections. If other invalid lines remain, return
409 without changes. For multiple invalid lines, creating a fresh cart is the
simple recovery path; partial recovery and batch edits are deferred. This keeps
successful mutation responses complete at the cost of less convenient recovery.

## Review and interview discussion

- PostgreSQL persistence and a server-issued UUID support guest carts without
  making identity/authentication a prerequisite; possession remains an access
  boundary that implementers must respect.
- Server validation protects both money and relationships: valid IDs alone do
  not prove ownership, availability, or a variant-specific price.
- Mutation-only expiration separates customer editing from polling; the exact
  deadline and atomic check matter more than a cleanup job's schedule.
- Separate lines preserve intent; grouped selections make configuration rules
  explicit. Neither replaces backend validation.
- Current cart prices and future order snapshots serve different needs: editable
  intent versus a durable transaction record.
- Display-ready responses reduce frontend coupling, while shared mutation
  responses cost larger payloads. Explicit stale-menu errors avoid fake totals.

Requirements reviewed: PostgreSQL/guest UUID storage; two states; 10-minute
mutation-only expiration and 404/410 behavior; separate lines and 1–20 quantity;
250-character instructions; grouped modifiers and all ownership/selection/price
checks; authoritative current decimal pricing; four requested totals; display
IDs and names; all five endpoints and examples; no schema or application changes.
Implementation verification remains future work, including expiration boundaries,
concurrent mutations, tampered pricing, required-group omissions, duplicate adds,
repricing, and stale-menu recovery. No runtime behavior is claimed by this design.
