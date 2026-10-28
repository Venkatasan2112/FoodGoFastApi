"""add_case_insensitive_category_unique_index

Revision ID: a76637e95b33
Revises: f2df1cbbdb2c
Create Date: 2026-10-28 10:14:51.316025

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a76637e95b33"
down_revision: str | Sequence[str] | None = "f2df1cbbdb2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("uq_categories_restaurant_id_name", "categories", type_="unique")
    op.create_index(
        "uq_categories_restaurant_id_lower_name",
        "categories",
        ["restaurant_id", sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_categories_restaurant_id_lower_name", table_name="categories")
    op.create_unique_constraint(
        "uq_categories_restaurant_id_name",
        "categories",
        ["restaurant_id", "name"],
    )

