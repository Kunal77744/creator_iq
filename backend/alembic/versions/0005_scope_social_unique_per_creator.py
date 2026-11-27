"""scope social_accounts unique constraint per creator

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-27

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_social_platform_user", "social_accounts", type_="unique")
    op.create_unique_constraint(
        "uq_creator_social_platform_user",
        "social_accounts",
        ["creator_id", "platform", "platform_user_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_creator_social_platform_user", "social_accounts", type_="unique")
    op.create_unique_constraint(
        "uq_social_platform_user",
        "social_accounts",
        ["platform", "platform_user_id"],
    )
