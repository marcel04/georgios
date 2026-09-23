"""create cart tables

Revision ID: c7a27f31d902
Revises: 9e4f00aee08d
Create Date: 2026-09-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c7a27f31d902"
down_revision: Union[str, Sequence[str], None] = "9e4f00aee08d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Explicit lifecycle: attaching this type to a table must not create it again.
cart_status = postgresql.ENUM(
    "ACTIVE", "EXPIRED", "CONVERTED", name="cart_status", create_type=False
)


def upgrade() -> None:
    cart_status.create(op.get_bind(), checkfirst=False)
    op.create_table(
        "carts",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "status", cart_status, server_default=sa.text("'ACTIVE'"), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_carts_status_expires_at", "carts", ["status", "expires_at"])
    op.create_table(
        "cart_items",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("menu_item_variant_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("special_instructions", sa.String(250), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity BETWEEN 1 AND 20", name="ck_cart_items_quantity_range"
        ),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["menu_item_variant_id"], ["menu_item_variants.id"], ondelete="NO ACTION"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])
    op.create_index(
        "ix_cart_items_menu_item_variant_id", "cart_items", ["menu_item_variant_id"]
    )
    op.create_table(
        "cart_item_modifier_options",
        sa.Column("cart_item_id", sa.UUID(), nullable=False),
        sa.Column("modifier_option_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cart_item_id"], ["cart_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["modifier_option_id"], ["modifier_options.id"], ondelete="NO ACTION"
        ),
        sa.PrimaryKeyConstraint("cart_item_id", "modifier_option_id"),
    )
    op.create_index(
        "ix_cart_item_modifier_options_modifier_option_id",
        "cart_item_modifier_options",
        ["modifier_option_id"],
    )
    # Reuse menu infrastructure; triggers update only their own row.
    for table in ("carts", "cart_items"):
        op.execute(f"""
            CREATE TRIGGER set_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)


def downgrade() -> None:
    for table in ("cart_items", "carts"):
        op.execute(f"DROP TRIGGER set_{table}_updated_at ON {table}")
    # Dropping tables also removes their indexes and constraints.
    op.drop_table("cart_item_modifier_options")
    op.drop_table("cart_items")
    op.drop_table("carts")
    cart_status.drop(op.get_bind(), checkfirst=False)
    # Keep set_updated_at(): menu tables still depend on it.
