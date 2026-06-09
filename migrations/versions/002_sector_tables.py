"""
ASIMNEXUS Sector Module Tables
================================
Creates database tables for Hospital, Hotel, Education, and Banking sectors,
plus Global Agent and Hardening audit tables.

Revision ID: 002
Revises: 001
Create Date: 2025-06-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create sector module tables."""

    # ═══════════════════════════════════════════════════════════════════════
    # HOSPITAL SECTOR
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "sector_hospitals",
        sa.Column("hospital_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("department_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("bed_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("staff_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sector_patients",
        sa.Column("patient_id", sa.String(64), primary_key=True),
        sa.Column("hospital_id", sa.String(64), sa.ForeignKey("sector_hospitals.hospital_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("blood_type", sa.String(8), nullable=True),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("department", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), server_default="admitted"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("admitted_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("discharged_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_sector_patients_hospital_id", "sector_patients", ["hospital_id"])
    op.create_index("ix_sector_patients_status", "sector_patients", ["status"])

    # ═══════════════════════════════════════════════════════════════════════
    # HOTEL SECTOR
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "sector_hotel_rooms",
        sa.Column("room_id", sa.String(64), primary_key=True),
        sa.Column("room_number", sa.String(16), nullable=False),
        sa.Column("room_type", sa.String(64), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("capacity", sa.Integer(), server_default=sa.text("2")),
        sa.Column("price_per_night", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("amenities", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="available"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_sector_hotel_rooms_status", "sector_hotel_rooms", ["status"])

    op.create_table(
        "sector_hotel_bookings",
        sa.Column("booking_id", sa.String(64), primary_key=True),
        sa.Column("room_id", sa.String(64), sa.ForeignKey("sector_hotel_rooms.room_id", ondelete="CASCADE"), nullable=False),
        sa.Column("guest_name", sa.String(256), nullable=False),
        sa.Column("guest_email", sa.String(256), nullable=True),
        sa.Column("guest_phone", sa.String(32), nullable=True),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("checked_in_at", sa.DateTime(), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_sector_hotel_bookings_room_id", "sector_hotel_bookings", ["room_id"])
    op.create_index("ix_sector_hotel_bookings_status", "sector_hotel_bookings", ["status"])

    # ═══════════════════════════════════════════════════════════════════════
    # EDUCATION SECTOR
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "sector_students",
        sa.Column("student_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("program", sa.String(128), nullable=True),
        sa.Column("gpa", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("credits_earned", sa.Integer(), server_default=sa.text("0")),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("enrolled_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("graduated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_sector_students_program", "sector_students", ["program"])
    op.create_index("ix_sector_students_status", "sector_students", ["status"])

    op.create_table(
        "sector_courses",
        sa.Column("course_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("code", sa.String(32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("level", sa.String(32), nullable=True),
        sa.Column("credits", sa.Integer(), server_default=sa.text("3")),
        sa.Column("department", sa.String(64), nullable=True),
        sa.Column("instructor", sa.String(256), nullable=True),
        sa.Column("capacity", sa.Integer(), server_default=sa.text("50")),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sector_enrollments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("student_id", sa.String(64), sa.ForeignKey("sector_students.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(64), sa.ForeignKey("sector_courses.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), server_default="enrolled"),
        sa.Column("grade", sa.String(4), nullable=True),
        sa.Column("enrolled_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # BANKING SECTOR
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "sector_bank_accounts",
        sa.Column("account_id", sa.String(64), primary_key=True),
        sa.Column("owner_name", sa.String(256), nullable=False),
        sa.Column("owner_id", sa.String(64), nullable=True),
        sa.Column("account_type", sa.String(32), server_default="savings"),
        sa.Column("currency", sa.String(8), server_default="NRS"),
        sa.Column("balance", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("kyc_verified", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_sector_bank_accounts_owner_id", "sector_bank_accounts", ["owner_id"])
    op.create_index("ix_sector_bank_accounts_status", "sector_bank_accounts", ["status"])

    op.create_table(
        "sector_transactions",
        sa.Column("transaction_id", sa.String(64), primary_key=True),
        sa.Column("account_id", sa.String(64), sa.ForeignKey("sector_bank_accounts.account_id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("balance_before", sa.Float(), nullable=True),
        sa.Column("balance_after", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_account", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_sector_transactions_account_id", "sector_transactions", ["account_id"])
    op.create_index("ix_sector_transactions_created_at", "sector_transactions", ["created_at"])

    # ═══════════════════════════════════════════════════════════════════════
    # GLOBAL AGENT TABLES
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "global_agents",
        sa.Column("agent_id", sa.String(64), primary_key=True),
        sa.Column("agent_type", sa.String(64), nullable=False),
        sa.Column("region_id", sa.String(64), nullable=False),
        sa.Column("capabilities", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("tasks_completed", sa.Integer(), server_default=sa.text("0")),
        sa.Column("registered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_heartbeat", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_global_agents_region_id", "global_agents", ["region_id"])
    op.create_index("ix_global_agents_status", "global_agents", ["status"])

    op.create_table(
        "global_regions",
        sa.Column("region_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("endpoint", sa.String(512), nullable=True),
        sa.Column("region_type", sa.String(32), server_default="auto"),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("agent_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("deployed", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("registered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_heartbeat", sa.DateTime(), server_default=sa.func.now()),
    )

    # ═══════════════════════════════════════════════════════════════════════
    # HARDENING / AUDIT TABLES
    # ═══════════════════════════════════════════════════════════════════════

    op.create_table(
        "security_audit_log",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", sa.String(128), nullable=True),
        sa.Column("actor_id", sa.String(64), nullable=True),
        sa.Column("allowed", sa.Boolean(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_security_audit_log_action", "security_audit_log", ["action"])
    op.create_index("ix_security_audit_log_created_at", "security_audit_log", ["created_at"])


def downgrade() -> None:
    """Drop sector tables in reverse order."""
    op.drop_table("security_audit_log")
    op.drop_table("global_regions")
    op.drop_table("global_agents")
    op.drop_table("sector_transactions")
    op.drop_table("sector_bank_accounts")
    op.drop_table("sector_enrollments")
    op.drop_table("sector_courses")
    op.drop_table("sector_students")
    op.drop_table("sector_hotel_bookings")
    op.drop_table("sector_hotel_rooms")
    op.drop_table("sector_patients")
    op.drop_table("sector_hospitals")
