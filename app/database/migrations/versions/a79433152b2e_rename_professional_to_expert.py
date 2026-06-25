"""rename_professional_to_expert

Revision ID: a79433152b2e
Revises: a0d46eda88ae
Create Date: 2026-05-07 17:13:34.004651

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a79433152b2e"
down_revision: Union[str, Sequence[str], None] = "a0d46eda88ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename table professionals -> experts
    op.rename_table("professionals", "experts")

    # Rename table professional_contracts -> expert_contracts
    op.rename_table("professional_contracts", "expert_contracts")

    # Rename table contract_activities -> expert_contract_activities
    op.rename_table("contract_activities", "expert_contract_activities")

    # Rename column professional_id -> expert_id in expert_contracts table
    op.alter_column("expert_contracts", "professional_id", new_column_name="expert_id")

    # Rename indexes
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.drop_index("ix_professionals_expert_name", table_name="experts")
        op.create_index("ix_experts_expert_name", "experts", ["expert_name"])

        op.drop_index("ix_professionals_id_number", table_name="experts")
        op.create_index("ix_experts_id_number", "experts", ["id_number"])

        op.drop_index("ix_contracts_professional_id", table_name="expert_contracts")
        op.create_index("ix_contracts_expert_id", "expert_contracts", ["expert_id"])

        op.drop_index("ix_contracts_order_id", table_name="expert_contracts")
        op.create_index(
            "ix_expert_contracts_order_id", "expert_contracts", ["order_id"]
        )

        op.drop_index(
            "ix_activities_contract_id", table_name="expert_contract_activities"
        )
        op.create_index(
            "ix_expert_contract_activities_contract_id",
            "expert_contract_activities",
            ["contract_id"],
        )
    else:
        op.execute(
            "ALTER INDEX ix_professionals_expert_name RENAME TO ix_experts_expert_name"
        )
        op.execute(
            "ALTER INDEX ix_professionals_id_number RENAME TO ix_experts_id_number"
        )
        op.execute(
            "ALTER INDEX ix_contracts_professional_id RENAME TO ix_contracts_expert_id"
        )
        op.execute(
            "ALTER INDEX ix_contracts_order_id RENAME TO ix_expert_contracts_order_id"
        )
        op.execute(
            "ALTER INDEX ix_activities_contract_id RENAME TO ix_expert_contract_activities_contract_id"
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert table names first
    op.rename_table("expert_contract_activities", "contract_activities")
    op.rename_table("expert_contracts", "professional_contracts")
    op.rename_table("experts", "professionals")

    # Revert column name
    op.alter_column(
        "professional_contracts", "expert_id", new_column_name="professional_id"
    )

    # Revert indexes
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.drop_index(
            "ix_expert_contract_activities_contract_id",
            table_name="contract_activities",
        )
        op.create_index(
            "ix_activities_contract_id", "contract_activities", ["contract_id"]
        )

        op.drop_index(
            "ix_expert_contracts_order_id", table_name="professional_contracts"
        )
        op.create_index("ix_contracts_order_id", "professional_contracts", ["order_id"])

        op.drop_index("ix_contracts_expert_id", table_name="professional_contracts")
        op.create_index(
            "ix_contracts_professional_id",
            "professional_contracts",
            ["professional_id"],
        )

        op.drop_index("ix_experts_id_number", table_name="professionals")
        op.create_index("ix_professionals_id_number", "professionals", ["id_number"])

        op.drop_index("ix_experts_expert_name", table_name="professionals")
        op.create_index(
            "ix_professionals_expert_name", "professionals", ["expert_name"]
        )
    else:
        op.execute(
            "ALTER INDEX ix_expert_contract_activities_contract_id RENAME TO ix_activities_contract_id"
        )
        op.execute(
            "ALTER INDEX ix_expert_contracts_order_id RENAME TO ix_contracts_order_id"
        )
        op.execute(
            "ALTER INDEX ix_contracts_expert_id RENAME TO ix_contracts_professional_id"
        )
        op.execute(
            "ALTER INDEX ix_experts_id_number RENAME TO ix_professionals_id_number"
        )
        op.execute(
            "ALTER INDEX ix_experts_expert_name RENAME TO ix_professionals_expert_name"
        )
