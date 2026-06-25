"""allow fractional working days

Revision ID: 6f0d9d3b2c1a
Revises: 328531f826bc
Create Date: 2026-05-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6f0d9d3b2c1a"
down_revision: Union[str, Sequence[str], None] = "328531f826bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("expert_contract_activities") as batch_op:
        batch_op.alter_column(
            "working_days",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using="working_days::double precision",
        )


def downgrade() -> None:
    with op.batch_alter_table("expert_contract_activities") as batch_op:
        batch_op.alter_column(
            "working_days",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="working_days::integer",
        )
