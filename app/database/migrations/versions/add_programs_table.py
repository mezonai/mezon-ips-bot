"""add programs table and refactor expert_contracts

Extract program fields (project_name, sum_activities, activity_purpose, end_date)
from expert_contracts into a new programs table. Contracts reference programs
via program_id FK.

Revision ID: add_programs_table
Revises: a79433152b2e
Create Date: 2026-05-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "add_programs_table"
down_revision: Union[str, Sequence[str], None] = "a79433152b2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create programs table
    op.create_table(
        "programs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("program_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("summary_activities", sa.String(length=500), nullable=True),
        sa.Column("activity_purpose", sa.String(length=255), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_code", name="uq_programs_program_code"),
        sa.Index("ix_programs_program_code", "program_code"),
    )

    # 2. Migrate existing contract data into programs
    # One program per abbreviated_project, using the latest contract's details.
    # For duplicates, suffix with a number to keep program_code unique.
    op.execute(
        """
        WITH ranked AS (
            SELECT
                abbreviated_project,
                COALESCE(project_name, abbreviated_project) AS name,
                end_date,
                sum_activities,
                activity_purpose,
                ROW_NUMBER() OVER (PARTITION BY abbreviated_project ORDER BY id DESC) AS rn
            FROM expert_contracts
            WHERE deleted_at IS NULL
              AND abbreviated_project IS NOT NULL
        )
        INSERT INTO programs (program_code, name, summary_activities, activity_purpose, end_date)
        SELECT
            abbreviated_project,
            name,
            sum_activities,
            activity_purpose,
            end_date
        FROM ranked
        WHERE rn = 1
        ON CONFLICT (program_code) DO NOTHING
        """
    )

    # 3. Add nullable program_id column
    op.add_column(
        "expert_contracts",
        sa.Column("program_id", sa.Integer(), nullable=True),
    )

    # 4. Populate program_id by matching abbreviated_project to program_code
    op.execute(
        """
        UPDATE expert_contracts
        SET program_id = (
            SELECT id FROM programs
            WHERE programs.program_code = expert_contracts.abbreviated_project
        )
        WHERE deleted_at IS NULL
        """
    )

    # 5. Make program_id NOT NULL, 6. Add FK, 7. Drop old columns
    with op.batch_alter_table("expert_contracts") as batch_op:
        batch_op.alter_column("program_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_expert_contracts_program_id",
            "programs",
            ["program_id"],
            ["id"],
        )
        batch_op.drop_column("project_name")
        batch_op.drop_column("sum_activities")
        batch_op.drop_column("activity_purpose")
        batch_op.drop_column("end_date")

    op.create_index("ix_contracts_program_id", "expert_contracts", ["program_id"])


def downgrade() -> None:
    # Re-add old columns
    with op.batch_alter_table("expert_contracts") as batch_op:
        batch_op.add_column(sa.Column("end_date", sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column("activity_purpose", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("sum_activities", sa.String(length=500), nullable=True)
        )
        batch_op.add_column(
            sa.Column("project_name", sa.String(length=200), nullable=True)
        )

    # Migrate data back from programs
    op.execute(
        """
        UPDATE expert_contracts
        SET
            end_date = (SELECT end_date FROM programs WHERE programs.id = expert_contracts.program_id),
            activity_purpose = (SELECT activity_purpose FROM programs WHERE programs.id = expert_contracts.program_id),
            sum_activities = (SELECT summary_activities FROM programs WHERE programs.id = expert_contracts.program_id),
            project_name = (SELECT name FROM programs WHERE programs.id = expert_contracts.program_id)
        WHERE program_id IS NOT NULL
        """
    )

    op.drop_index("ix_contracts_program_id", table_name="expert_contracts")

    # Fix nullability for downgrade, drop FK and program_id
    with op.batch_alter_table("expert_contracts") as batch_op:
        batch_op.alter_column(
            "end_date",
            nullable=False,
            server_default=sa.text("'2026-01-01'"),
        )
        batch_op.drop_constraint("fk_expert_contracts_program_id", type_="foreignkey")
        batch_op.drop_column("program_id")

    # Drop programs table
    op.drop_table("programs")
