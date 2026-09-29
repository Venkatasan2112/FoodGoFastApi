"""Add ForeignKey to users.role_id

Revision ID: fed1c858f386
Revises: aba738dccd85
Create Date: 2026-09-28 10:15:24.787563

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "fed1c858f386"
down_revision: str | Sequence[str] | None = "aba738dccd85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration originally duplicated the fk_users_role_id_roles foreign key
    # which was already created in aba738dccd85. To avoid errors without rewriting
    # history, we make this a no-op.


def downgrade() -> None:
    """Downgrade schema."""
    # No-op because upgrade is a no-op.
