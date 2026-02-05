"""create tasks table

Revision ID: 20260205_01
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260205_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Criar tabela tasks e ENUM task_status"""
    
    conn = op.get_bind()
    
    # Verificar se o tipo já existe
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'task_status'")
    ).fetchone()
    
    if not result:
        # Criar o ENUM type se não existir
        task_status_enum = postgresql.ENUM(
            'pending', 'processing', 'completed', 'failed',
            name='task_status',
            create_type=True
        )
        task_status_enum.create(conn)
    
    # Criar a tabela tasks
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'status',
            postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='task_status', create_type=False),
            nullable=False,
            server_default='pending'
        ),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )


def downgrade():
    """Dropar tabela tasks e ENUM task_status de forma idempotente"""
    
    conn = op.get_bind()
    
    # Dropar tabela se existir
    conn.execute(sa.text('DROP TABLE IF EXISTS tasks CASCADE'))
    
    # Dropar ENUM type se existir
    conn.execute(sa.text('DROP TYPE IF EXISTS task_status CASCADE'))
