"""NPC combat sheet fields and battlemap grid size

Adds a lightweight "combat sheet" to WorldNPCTable (resistances,
vulnerabilities, simple named actions -- all game-agnostic JSON, per
AGENTS.md §8) and variable battlemap grid dimensions to GameSession
(replacing the previously hardcoded 15x15 frontend grid).

Revision ID: 1d9b3c682318
Revises: 09e4c814e6af
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1d9b3c682318'
down_revision: Union[str, Sequence[str], None] = '09e4c814e6af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('world_npc', schema=None) as batch_op:
        batch_op.add_column(sa.Column('resistances', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('vulnerabilities', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('actions', sa.JSON(), nullable=False, server_default='[]'))

    with op.batch_alter_table('game_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('grid_width', sa.Integer(), nullable=False, server_default='15'))
        batch_op.add_column(sa.Column('grid_height', sa.Integer(), nullable=False, server_default='15'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('game_session', schema=None) as batch_op:
        batch_op.drop_column('grid_height')
        batch_op.drop_column('grid_width')

    with op.batch_alter_table('world_npc', schema=None) as batch_op:
        batch_op.drop_column('actions')
        batch_op.drop_column('vulnerabilities')
        batch_op.drop_column('resistances')
