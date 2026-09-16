from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aba738dccd85'
down_revision: Union[str, Sequence[str], None] = '6ad6169597c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1. Create roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name")
    )

    # 2. Insert default roles
    op.execute("""
        INSERT INTO roles (id, name)
        VALUES
        (gen_random_uuid(), 'USER'),
        (gen_random_uuid(), 'ADMIN')
    """)

    # 3. Add role_id temporarily as nullable
    op.add_column(
        "users",
        sa.Column("role_id", sa.UUID(), nullable=True)
    )

    # 4. Convert old role values to role_id
    op.execute("""
        UPDATE users
        SET role_id = roles.id
        FROM roles
        WHERE users.role = roles.name
    """)

    # 5. Make role_id required
    op.alter_column(
        "users",
        "role_id",
        existing_type=sa.UUID(),
        nullable=False
    )

    # 6. Add foreign key
    op.create_foreign_key(
        "fk_users_role_id_roles",
        "users",
        "roles",
        ["role_id"],
        ["id"]
    )

    # 7. Remove old role column
    op.drop_column("users", "role")


def downgrade() -> None:

    # 1. Add old role column back
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=100), nullable=True)
    )

    # 2. Convert role_id back to role
    op.execute("""
        UPDATE users
        SET role = roles.name
        FROM roles
        WHERE users.role_id = roles.id
    """)

    # 3. Make old role required
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=100),
        nullable=False
    )

    # 4. Remove foreign key
    op.drop_constraint(
        "fk_users_role_id_roles",
        "users",
        type_="foreignkey"
    )

    # 5. Remove role_id
    op.drop_column("users", "role_id")

    # 6. Remove roles table
    op.drop_table("roles")