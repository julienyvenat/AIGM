"""GameSession voice_enabled opt-in flag

Adds a `voice_enabled` boolean to GameSession, defaulting to False. TTS
(OpenAI audio.speech) generation costs money per call and isn't
budget-approved for always-on use, so it stays opt-in per session (see
PUT /sessions/{id}/voice and background_tts_generation in main.py).

Revision ID: e1faab52b267
Revises: 1d9b3c682318
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e1faab52b267'
down_revision: Union[str, Sequence[str], None] = '1d9b3c682318'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('game_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('voice_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('game_session', schema=None) as batch_op:
        batch_op.drop_column('voice_enabled')
