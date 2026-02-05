"""create tasks table

Revision ID: 20260205_01
Revises: 
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260205_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    task_status = sa.Enum(
        "pending",
        "processing",
        "completed",
        "failed",
        name="task_status",
    )
    task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", task_status, nullable=False, server_default="pending"),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=True),
        sa.Column("estimated_duration", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tasks")
    task_status = sa.Enum(
        "pending",
        "processing",
        "completed",
        "failed",
        name="task_status",
    )
    task_status.drop(op.get_bind(), checkfirst=True)
