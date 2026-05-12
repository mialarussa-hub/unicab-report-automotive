"""Add l3_synthesis JSONB column to scraping_sessions for L3 user-voice minireport.

Revision ID: 003
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scraping_sessions",
        sa.Column("l3_synthesis", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scraping_sessions", "l3_synthesis")
