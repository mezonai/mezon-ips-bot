"""add start_date to programs

Revision ID: 9b7d1a2c4e5f
Revises: 6f0d9d3b2c1a
Create Date: 2026-05-17 09:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b7d1a2c4e5f"
down_revision: Union[str, Sequence[str], None] = "6f0d9d3b2c1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("programs", sa.Column("start_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("programs", "start_date")
