"""create menu modifier tables

Revision ID: 9e4f00aee08d
Revises: 361f81bb87ba
Create Date: 2026-09-14 16:54:40.994308

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9e4f00aee08d"
down_revision: Union[str, Sequence[str], None] = "361f81bb87ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The referenced composite key must exist before the pricing foreign key.
    op.create_unique_constraint(
        "uq_menu_item_variants_id_item", "menu_item_variants", ["id", "menu_item_id"]
    )
    op.create_table(
        "modifier_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("min_selections", sa.Integer(), nullable=False),
        sa.Column("max_selections", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
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
            "max_selections >= 0", name="ck_modifier_groups_max_nonnegative"
        ),
        sa.CheckConstraint(
            "max_selections >= min_selections",
            name="ck_modifier_groups_selection_range",
        ),
        sa.CheckConstraint(
            "min_selections >= 0", name="ck_modifier_groups_min_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["menu_item_id"], ["menu_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "menu_item_id", name="uq_modifier_groups_id_item"),
        sa.UniqueConstraint(
            "menu_item_id", "display_order", name="uq_modifier_groups_item_order"
        ),
        sa.UniqueConstraint(
            "menu_item_id", "name", name="uq_modifier_groups_item_name"
        ),
    )
    op.create_table(
        "modifier_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("modifier_group_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column(
            "is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
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
        sa.ForeignKeyConstraint(
            ["modifier_group_id", "menu_item_id"],
            ["modifier_groups.id", "modifier_groups.menu_item_id"],
            name="fk_modifier_options_group_item",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "menu_item_id", name="uq_modifier_options_id_item"),
        sa.UniqueConstraint(
            "modifier_group_id", "display_order", name="uq_modifier_options_group_order"
        ),
        sa.UniqueConstraint(
            "modifier_group_id", "name", name="uq_modifier_options_group_name"
        ),
    )
    op.create_table(
        "modifier_option_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("modifier_option_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_variant_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column(
            "price_adjustment", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.CheckConstraint(
            "price_adjustment >= 0", name="ck_modifier_option_prices_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["menu_item_variant_id", "menu_item_id"],
            ["menu_item_variants.id", "menu_item_variants.menu_item_id"],
            name="fk_modifier_option_prices_variant_item",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["modifier_option_id", "menu_item_id"],
            ["modifier_options.id", "modifier_options.menu_item_id"],
            name="fk_modifier_option_prices_option_item",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "modifier_option_id",
            "menu_item_variant_id",
            name="uq_modifier_option_prices_option_variant",
        ),
    )
    # Reuse the timestamp function installed by the initial menu migration.
    for table in ("modifier_groups", "modifier_options"):
        op.execute(f"""
            CREATE TRIGGER set_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    for table in ("modifier_options", "modifier_groups"):
        op.execute(f"DROP TRIGGER IF EXISTS set_{table}_updated_at ON {table}")
    # Keep set_updated_at(): existing menu tables still use it.
    op.drop_table("modifier_option_prices")
    op.drop_table("modifier_options")
    op.drop_table("modifier_groups")
    op.drop_constraint(
        "uq_menu_item_variants_id_item", "menu_item_variants", type_="unique"
    )
    # ### end Alembic commands ###
