"""create users and refresh tokens

Revision ID: 20260206_01
Revises: 20260205_01
Create Date: 2026-02-06

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260206_01"
down_revision = "20260205_01"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'user_role'"))
    if not result.fetchone():
        user_role_enum = postgresql.ENUM("user", "admin", name="user_role", create_type=True)
        user_role_enum.create(conn)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "admin", name="user_role", create_type=False),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.add_column(
        "tasks",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_tasks_owner_id_users",
        "tasks",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tasks_owner_id", "tasks", ["owner_id"])


def downgrade():
    conn = op.get_bind()

    op.drop_index("ix_tasks_owner_id", table_name="tasks")
    op.drop_constraint("fk_tasks_owner_id_users", "tasks", type_="foreignkey")
    op.drop_column("tasks", "owner_id")

    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    conn.execute(sa.text("DROP TYPE IF EXISTS user_role CASCADE"))
