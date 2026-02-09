"""Add manual override columns and table

Revision ID: 002_manual_override
Revises: 001_initial
Create Date: 2026-01-26 15:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic
revision: str = "002_manual_override"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add manual override columns and create the manual_overrides table."""

    # Add new columns to devices table for manual labeling
    op.add_column(
        "devices",
        sa.Column("name_manual", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column("vendor_manual", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column("manual_override_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column("manual_override_by", sa.String(length=100), nullable=True),
    )

    # Add hybrid scanner metadata columns (may already exist, use batch mode for SQLite)
    # Using try/except pattern since SQLite doesn't support IF NOT EXISTS for columns
    try:
        op.add_column(
            "devices",
            sa.Column("discovery_source", sa.String(length=50), nullable=True),
        )
    except Exception:
        pass  # Column may already exist

    try:
        op.add_column(
            "devices",
            sa.Column("freshness_score", sa.Integer(), nullable=True),
        )
    except Exception:
        pass  # Column may already exist

    # Create manual_overrides table for fingerprint-based label reuse
    op.create_table(
        "manual_overrides",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fingerprint_key", sa.String(length=64), nullable=False),
        sa.Column("manual_name", sa.String(length=255), nullable=True),
        sa.Column("manual_vendor", sa.String(length=255), nullable=True),
        sa.Column("source_mac", sa.String(length=17), nullable=True),
        sa.Column("source_ip", sa.String(length=45), nullable=True),
        sa.Column("fingerprint_components", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for manual_overrides table
    op.create_index(
        "ix_manual_overrides_fingerprint_key",
        "manual_overrides",
        ["fingerprint_key"],
        unique=True,
    )


def downgrade() -> None:
    """Remove manual override columns and table."""
    # Drop manual_overrides table
    op.drop_index("ix_manual_overrides_fingerprint_key", table_name="manual_overrides")
    op.drop_table("manual_overrides")

    # Drop columns from devices table
    op.drop_column("devices", "freshness_score")
    op.drop_column("devices", "discovery_source")
    op.drop_column("devices", "manual_override_by")
    op.drop_column("devices", "manual_override_at")
    op.drop_column("devices", "vendor_manual")
    op.drop_column("devices", "name_manual")
