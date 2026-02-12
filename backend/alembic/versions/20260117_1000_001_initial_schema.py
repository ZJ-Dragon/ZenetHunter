"""Initial database schema for ZenetHunter

Revision ID: 001_initial
Revises:
Create Date: 2026-01-17 10:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create devices table
    op.create_table(
        "devices",
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column(
            "type",
            sa.Enum("UNKNOWN", "ROUTER", "PC", "MOBILE", "IOT", name="devicetypeenum"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("ONLINE", "OFFLINE", "BLOCKED", name="devicestatusenum"),
            nullable=False,
        ),
        sa.Column(
            "active_defense_status",
            sa.Enum("IDLE", "RUNNING", "STOPPED", "FAILED", name="activedefensestatus"),
            nullable=False,
        ),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("alias", sa.String(length=255), nullable=True),
        sa.Column("vendor_guess", sa.String(length=255), nullable=True),
        sa.Column("model_guess", sa.String(length=255), nullable=True),
        sa.Column("recognition_confidence", sa.Integer(), nullable=True),
        sa.Column("recognition_evidence", sa.Text(), nullable=True),
        sa.Column(
            "recognition_manual_override",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
        sa.PrimaryKeyConstraint("mac"),
    )

    # Create indexes for devices table
    op.create_index("ix_devices_mac", "devices", ["mac"])
    op.create_index("ix_devices_ip", "devices", ["ip"])
    op.create_index("ix_devices_last_seen", "devices", ["last_seen"])
    op.create_index("ix_devices_status", "devices", ["status"])

    # Create device_fingerprints table
    op.create_table(
        "device_fingerprints",
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column("dhcp_fingerprint", sa.Text(), nullable=True),
        sa.Column("dhcp_vendor_class", sa.String(length=255), nullable=True),
        sa.Column("dhcp_hostname", sa.String(length=255), nullable=True),
        sa.Column("mdns_services", sa.Text(), nullable=True),
        sa.Column("mdns_hostname", sa.String(length=255), nullable=True),
        sa.Column("ssdp_devices", sa.Text(), nullable=True),
        sa.Column("ssdp_server", sa.String(length=255), nullable=True),
        sa.Column("http_user_agent", sa.String(length=512), nullable=True),
        sa.Column("open_ports", sa.Text(), nullable=True),
        sa.Column("tcp_fingerprint", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mac"], ["devices.mac"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("mac"),
    )

    # Create event_logs table
    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "level",
            sa.Enum("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", name="loglevel"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("device_mac", sa.String(length=17), nullable=True),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for event_logs table
    op.create_index("ix_event_logs_timestamp", "event_logs", ["timestamp"])
    op.create_index("ix_event_logs_level", "event_logs", ["level"])
    op.create_index("ix_event_logs_source", "event_logs", ["source"])
    op.create_index("ix_event_logs_event_type", "event_logs", ["event_type"])
    op.create_index("ix_event_logs_device_mac", "event_logs", ["device_mac"])
    op.create_index("ix_event_logs_correlation_id", "event_logs", ["correlation_id"])

    # Create trust_lists table
    op.create_table(
        "trust_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mac", sa.String(length=17), nullable=False),
        sa.Column(
            "list_type",
            sa.Enum("WHITELIST", "BLACKLIST", "GRAYLIST", name="listtype"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("added_by", sa.String(length=100), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for trust_lists table
    op.create_index("ix_trust_lists_mac", "trust_lists", ["mac"])
    op.create_index("ix_trust_lists_list_type", "trust_lists", ["list_type"])
    op.create_index("ix_trust_lists_is_active", "trust_lists", ["is_active"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_trust_lists_is_active", table_name="trust_lists")
    op.drop_index("ix_trust_lists_list_type", table_name="trust_lists")
    op.drop_index("ix_trust_lists_mac", table_name="trust_lists")
    op.drop_table("trust_lists")

    op.drop_index("ix_event_logs_correlation_id", table_name="event_logs")
    op.drop_index("ix_event_logs_device_mac", table_name="event_logs")
    op.drop_index("ix_event_logs_event_type", table_name="event_logs")
    op.drop_index("ix_event_logs_source", table_name="event_logs")
    op.drop_index("ix_event_logs_level", table_name="event_logs")
    op.drop_index("ix_event_logs_timestamp", table_name="event_logs")
    op.drop_table("event_logs")

    op.drop_table("device_fingerprints")

    op.drop_index("ix_devices_status", table_name="devices")
    op.drop_index("ix_devices_last_seen", table_name="devices")
    op.drop_index("ix_devices_ip", table_name="devices")
    op.drop_index("ix_devices_mac", table_name="devices")
    op.drop_table("devices")
