"""add tracking_number to orders

Revision ID: 30bb282a56ef
Revises: 138da28f5512
Create Date: 2026-07-22 16:51:25.205379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30bb282a56ef'
down_revision: Union[str, Sequence[str], None] = '138da28f5512'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "orders",
        sa.Column("tracking_number", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "tracking_number")
