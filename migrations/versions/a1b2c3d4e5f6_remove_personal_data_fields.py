"""remove personal data fields

Epic 1 / task 1.6: drop legacy personal-data columns from
``orders``, ``users`` and ``document_types`` if they still exist.

The current SQLAlchemy models never referenced these columns, but older
deployments may carry them. This migration is idempotent and uses
``batch_alter_table`` so it is compatible with SQLite.

Revision ID: a1b2c3d4e5f6
Revises: 30bb282a56ef
Create Date: 2026-09-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "30bb282a56ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Personal-data columns to remove per table (if present).
PD_COLUMNS: dict[str, tuple[str, ...]] = {
    "orders": (
        "passport_number",
        "inn",
        "snils",
        "registration_address",
        "date_of_birth",
    ),
    "users": (
        "passport_number",
        "inn",
        "snils",
        "registration_address",
        "date_of_birth",
    ),
    "document_types": (
        "passport_number",
        "inn",
        "snils",
        "registration_address",
        "date_of_birth",
    ),
}


def _existing_columns(table_name: str) -> set[str]:
    """Return the set of column names currently present in *table*."""
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    """Drop legacy personal-data columns when present (idempotent)."""
    for table, columns in PD_COLUMNS.items():
        to_drop = [c for c in columns if c in _existing_columns(table)]
        if not to_drop:
            continue
        with op.batch_alter_table(table) as batch_op:
            for column in to_drop:
                batch_op.drop_column(column)


def downgrade() -> None:
    """No-op: personal-data columns are intentionally not restored."""
    pass