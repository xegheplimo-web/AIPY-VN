"""Add database indexes for performance

Revision ID: b8f3d2e1c4a5
Revises: 61c6f0be4b51
Create Date: 2026-06-07 21:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8f3d2e1c4a5"
down_revision: Union[str, Sequence[str], None] = "61c6f0be4b51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add performance indexes."""
    # Store indexes
    op.create_index("idx_store_status", "stores", ["status"])
    op.create_index("idx_store_location", "stores", ["latitude", "longitude"])
    op.create_index("idx_store_industry", "stores", ["industry"])
    op.create_index("idx_store_is_open", "stores", ["is_open_now"])

    # Product indexes
    op.create_index("idx_product_store_id", "products", ["store_id"])
    op.create_index("idx_product_status", "products", ["status"])
    op.create_index("idx_product_name", "products", ["name"])
    op.create_index("idx_product_category", "products", ["category_id"])
    op.create_index("idx_product_stock", "products", ["stock"])

    # User indexes
    op.create_index("idx_user_email", "users", ["email"])
    op.create_index("idx_user_role", "users", ["role"])
    op.create_index("idx_user_is_active", "users", ["is_active"])

    # Order indexes
    op.create_index("idx_order_user_id", "orders", ["user_id"])
    op.create_index("idx_order_store_id", "orders", ["store_id"])
    op.create_index("idx_order_status", "orders", ["status"])
    op.create_index("idx_order_number", "orders", ["order_number"])
    op.create_index("idx_order_created_at", "orders", ["created_at"])


def downgrade() -> None:
    """Downgrade schema - remove performance indexes."""
    # Store indexes
    op.drop_index("idx_store_status", "stores")
    op.drop_index("idx_store_location", "stores")
    op.drop_index("idx_store_industry", "stores")
    op.drop_index("idx_store_is_open", "stores")

    # Product indexes
    op.drop_index("idx_product_store_id", "products")
    op.drop_index("idx_product_status", "products")
    op.drop_index("idx_product_name", "products")
    op.drop_index("idx_product_category", "products")
    op.drop_index("idx_product_stock", "products")

    # User indexes
    op.drop_index("idx_user_email", "users")
    op.drop_index("idx_user_role", "users")
    op.drop_index("idx_user_is_active", "users")

    # Order indexes
    op.drop_index("idx_order_user_id", "orders")
    op.drop_index("idx_order_store_id", "orders")
    op.drop_index("idx_order_status", "orders")
    op.drop_index("idx_order_number", "orders")
    op.drop_index("idx_order_created_at", "orders")
