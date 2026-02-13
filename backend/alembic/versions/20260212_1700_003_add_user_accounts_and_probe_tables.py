"""Add user_accounts, manual profiles, and probe observations

Revision ID: 003_add_user_accounts_and_probe_tables
Revises: 002_manual_override
Create Date: 2026-02-12 17:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_user_accounts_and_probe_tables"
down_revision: str | None = "002_manual_override"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create missing tables and columns if they do not exist."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # user_accounts table
    if not inspector.has_table("user_accounts"):
        op.create_table(
            "user_accounts",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("username", sa.String(length=255), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column(
                "role",
                sa.Enum("admin", "guest", name="userrole"),
                nullable=False,
                server_default="admin",
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_user_accounts_username", "user_accounts", ["username"], unique=True
        )

    # device_manual_profiles table
    if not inspector.has_table("device_manual_profiles"):
        op.create_table(
            "device_manual_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("manual_name", sa.String(length=255), nullable=True),
            sa.Column("manual_vendor", sa.String(length=255), nullable=True),
            sa.Column("fingerprint_key", sa.String(length=64), nullable=True),
            sa.Column("match_keys", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("mac", sa.String(length=17), nullable=True),
            sa.Column("ip_hint", sa.String(length=45), nullable=True),
            sa.Column("keywords", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("fingerprint_key", name="uq_device_manual_profiles_fp"),
        )
        op.create_index(
            "ix_device_manual_profiles_fingerprint_key",
            "device_manual_profiles",
            ["fingerprint_key"],
        )
        op.create_index(
            "ix_device_manual_profiles_mac", "device_manual_profiles", ["mac"]
        )

    # Add manual_profile_id to devices if missing
    device_columns = {col["name"] for col in inspector.get_columns("devices")}
    if "manual_profile_id" not in device_columns:
        op.add_column(
            "devices",
            sa.Column("manual_profile_id", sa.Integer(), nullable=True, index=True),
        )

    # probe_observations table
    if not inspector.has_table("probe_observations"):
        op.create_table(
            "probe_observations",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("device_mac", sa.String(length=17), nullable=False, index=True),
            sa.Column("scan_run_id", sa.String(length=36), nullable=True, index=True),
            sa.Column("protocol", sa.String(length=64), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("key_fields", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("keywords", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("keyword_hits", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("raw_summary", sa.Text(), nullable=True),
            sa.Column(
                "redaction_level",
                sa.String(length=32),
                nullable=False,
                server_default="standard",
            ),
        )
        op.create_index(
            "ix_probe_observations_device_mac",
            "probe_observations",
            ["device_mac"],
        )
        op.create_index(
            "ix_probe_observations_scan_run_id",
            "probe_observations",
            ["scan_run_id"],
        )
        op.create_index(
            "ix_probe_observations_protocol",
            "probe_observations",
            ["protocol"],
        )


def downgrade() -> None:
    """Drop tables/columns created in upgrade."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("probe_observations"):
        op.drop_index("ix_probe_observations_protocol", table_name="probe_observations")
        op.drop_index(
            "ix_probe_observations_scan_run_id", table_name="probe_observations"
        )
        op.drop_index(
            "ix_probe_observations_device_mac", table_name="probe_observations"
        )
        op.drop_table("probe_observations")

    if inspector.has_table("user_accounts"):
        op.drop_index("ix_user_accounts_username", table_name="user_accounts")
        op.drop_table("user_accounts")

    if inspector.has_table("device_manual_profiles"):
        op.drop_index(
            "ix_device_manual_profiles_fingerprint_key",
            table_name="device_manual_profiles",
        )
        op.drop_index(
            "ix_device_manual_profiles_mac", table_name="device_manual_profiles"
        )
        op.drop_table("device_manual_profiles")

    device_columns = {col["name"] for col in inspector.get_columns("devices")}
    if "manual_profile_id" in device_columns:
        op.drop_column("devices", "manual_profile_id")
