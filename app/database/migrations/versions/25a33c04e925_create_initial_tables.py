"""create initial tables

Revision ID: 25a33c04e925
Revises: 
Create Date: 2025-08-18 02:48:52.635957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25a33c04e925'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates the initial tables for the application."""
    op.create_table(
        'chats',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('ts', sa.Time(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'classes',
        sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('class_id', sa.String(), nullable=False),
        sa.Column('semester', sa.String(), nullable=True),
        sa.Column('chat_id', sa.String(), nullable=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.UniqueConstraint('class_id', name='uq_class_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'absences',
        sa.Column('chat_id', sa.String(), nullable=True),
        sa.Column('class_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('counter', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], )
    )


def downgrade() -> None:
    """Drops all tables."""
    op.drop_table('absences')
    op.drop_table('classes')
    op.drop_table('chats')
