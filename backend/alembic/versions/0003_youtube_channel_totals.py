"""store real channel totals + live flag on social_accounts

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add lifetime view/video totals, live sync flag, and sync timestamp to social_accounts."""
    with op.batch_alter_table('social_accounts') as b:
        b.add_column(sa.Column('total_views', sa.BigInteger(), nullable=False, server_default='0'))
        b.add_column(sa.Column('video_count', sa.Integer(), nullable=False, server_default='0'))
        b.add_column(sa.Column('is_live', sa.Boolean(), nullable=False, server_default=sa.false()))
        b.add_column(sa.Column('last_synced_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove channel total and sync tracking columns from social_accounts."""
    with op.batch_alter_table('social_accounts') as b:
        b.drop_column('last_synced_at')
        b.drop_column('is_live')
        b.drop_column('video_count')
        b.drop_column('total_views')
