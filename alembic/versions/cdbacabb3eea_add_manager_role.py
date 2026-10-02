"""add_manager_role

Revision ID: cdbacabb3eea
Revises: c041ab8b8650
Create Date: 2026-10-02 13:24:44.561308

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cdbacabb3eea"
down_revision: str | Sequence[str] | None = "c041ab8b8650"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        INSERT INTO roles (id, name)
        SELECT gen_random_uuid(), 'MANAGER'
        WHERE NOT EXISTS (
            SELECT 1 FROM roles WHERE name = 'MANAGER'
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DELETE FROM roles
        WHERE name = 'MANAGER'
        AND NOT EXISTS (
            SELECT 1 FROM users WHERE users.role_id = roles.id
        );
    """)
