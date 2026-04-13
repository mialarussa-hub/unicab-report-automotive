"""Add official_info JSONB column to scraping_results for L1 brand communication data.

Revision ID: 001
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scraping_results",
        sa.Column("official_info", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scraping_results", "official_info")
