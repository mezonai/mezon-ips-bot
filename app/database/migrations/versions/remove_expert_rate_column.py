"""remove rate column from experts

The rate field is now stored on each ContractActivity instead of denormalized
on the Expert table.

Revision ID: remove_expert_rate_column
Revises: add_programs_table
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "remove_expert_rate_column"
down_revision: Union[str, Sequence[str], None] = "add_programs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("experts", "rate")


def downgrade() -> None:
    op.add_column(
        "experts",
        sa.Column("rate", sa.Float(), nullable=True),
    )
