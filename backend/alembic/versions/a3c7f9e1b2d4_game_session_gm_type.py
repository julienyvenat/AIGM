"""GameSession gm_type (AI or HUMAN game master)

Adds a `gm_type` column to GameSession, defaulting to 'AI' (the pre-existing
behavior: the AI narrator/arbitrator agents autonomously drive the session).
When set to 'HUMAN', `host_id` doubles as the human GM's user id -- see the
comment on GameSession.gm_type in models.py for why no separate
`gm_user_id` column was added.

Revision ID: a3c7f9e1b2d4
Revises: e1faab52b267
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a3c7f9e1b2d4'
down_revision: Union[str, Sequence[str], None] = 'e1faab52b267'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('game_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gm_type', sa.String(), nullable=False, server_default='AI'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('game_session', schema=None) as batch_op:
        batch_op.drop_column('gm_type')
