"""
ASIMNEXUS Initial Database Schema
==================================
Creates the foundational tables: users, conversations, api_keys, sessions,
identities, contracts, jobs, and system events.

Revision ID: 001
Revises: None
Create Date: 2025-06-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    
    # ─── Users table ──────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("username", sa.String(128), unique=True, nullable=False),
        sa.Column("email", sa.String(256), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), server_default="user"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ─── Tokens / Sessions table ───────────────────────────────────────────
    op.create_table(
        "auth_tokens",
        sa.Column("token", sa.String(128), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default=sa.text("0")),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_index("ix_auth_tokens_expires_at", "auth_tokens", ["expires_at"])

    # ─── Conversations / Messages table ─────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("tokens", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_created_at", "conversations", ["created_at"])

    # ─── API Keys table ────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("key_value", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])

    # ─── Digital Identities table ───────────────────────────────────────────
    op.create_table(
        "identities",
        sa.Column("did", sa.String(128), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("identity_type", sa.String(32), server_default="personal"),
        sa.Column("did_document", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_identities_user_id", "identities", ["user_id"])

    # ─── Smart Contracts table ──────────────────────────────────────────────
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("creator_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("terms", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="proposed"),
        sa.Column("gate_2_verified", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("signed_by_creator", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("signed_by_counterparty", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_contracts_creator_id", "contracts", ["creator_id"])
    op.create_index("ix_contracts_status", "contracts", ["status"])

    # ─── Jobs / Marketplace table ───────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("poster_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("budget", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("currency", sa.String(8), server_default="NRS"),
        sa.Column("status", sa.String(32), server_default="open"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_jobs_poster_id", "jobs", ["poster_id"])
    op.create_index("ix_jobs_category", "jobs", ["category"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # ─── Job Applications table ─────────────────────────────────────────────
    op.create_table(
        "job_applications",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("job_id", sa.String(64), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("applicant_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proposal", sa.Text(), nullable=True),
        sa.Column("bid_amount", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ─── System Events / Audit Log table ────────────────────────────────────
    op.create_table(
        "system_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), server_default="info"),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_system_events_event_type", "system_events", ["event_type"])
    op.create_index("ix_system_events_created_at", "system_events", ["created_at"])

    # ─── Settings / Configuration table ─────────────────────────────────────
    op.create_table(
        "settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ─── Bug Reports table ──────────────────────────────────────────────────
    op.create_table(
        "bug_reports",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(16), server_default="medium"),
        sa.Column("status", sa.String(32), server_default="open"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("bug_reports")
    op.drop_table("settings")
    op.drop_table("system_events")
    op.drop_table("job_applications")
    op.drop_table("jobs")
    op.drop_table("contracts")
    op.drop_table("identities")
    op.drop_table("api_keys")
    op.drop_table("conversations")
    op.drop_table("auth_tokens")
    op.drop_table("users")
