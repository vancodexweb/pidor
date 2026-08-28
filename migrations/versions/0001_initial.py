"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "bots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_bot_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("token_encrypted", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.telegram_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_bots_owner_id", "bots", ["owner_id"])
    op.create_index("ix_bots_telegram_bot_id", "bots", ["telegram_bot_id"], unique=True)
    op.create_unique_constraint("uq_bots_username", "bots", ["username"])

    op.create_table(
        "bot_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("welcome_text", sa.Text(), nullable=False),
        sa.Column("welcome_sticker_file_id", sa.String(length=255), nullable=True),
        sa.Column("welcome_image_file_id", sa.String(length=255), nullable=True),
        sa.Column("start_button_text", sa.String(length=64), nullable=False),
        sa.Column("name_question", sa.Text(), nullable=False),
        sa.Column("phone_question", sa.Text(), nullable=False),
        sa.Column("confirmation_text", sa.Text(), nullable=False),
        sa.Column("success_text", sa.Text(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("bot_id", name="uq_bot_settings_bot_id"),
    )

    # create_type=False: the type is created explicitly below, so create_table()
    # must not also try to auto-create it (it would emit a second, conflicting
    # CREATE TYPE for the same inline column). This must be the dialect-specific
    # postgresql.ENUM, not the generic sa.Enum — create_type is silently dropped
    # when a generic Enum gets adapted to Postgres's native type during DDL.
    slot_status = PGEnum("available", "booked", "blocked", name="slot_status", create_type=False)
    slot_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "time_slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("status", slot_status, nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("bot_id", "date", "start_time", name="uq_slot_bot_date_time"),
    )
    op.create_index("ix_time_slots_bot_date", "time_slots", ["bot_id", "date"])

    booking_status = PGEnum("confirmed", "cancelled", "completed", name="booking_status", create_type=False)
    booking_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot_id", sa.Integer(), nullable=False),
        sa.Column("slot_id", sa.Integer(), nullable=False),
        sa.Column("client_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["bot_id"], ["bots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["time_slots.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_bookings_bot_id", "bookings", ["bot_id"])
    op.create_index(
        "uq_booking_active_slot",
        "bookings",
        ["slot_id"],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed'"),
    )


def downgrade() -> None:
    op.drop_index("uq_booking_active_slot", table_name="bookings")
    op.drop_index("ix_bookings_bot_id", table_name="bookings")
    op.drop_table("bookings")
    PGEnum(name="booking_status", create_type=False).drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_time_slots_bot_date", table_name="time_slots")
    op.drop_table("time_slots")
    PGEnum(name="slot_status", create_type=False).drop(op.get_bind(), checkfirst=True)

    op.drop_table("bot_settings")

    op.drop_constraint("uq_bots_username", "bots", type_="unique")
    op.drop_index("ix_bots_telegram_bot_id", table_name="bots")
    op.drop_index("ix_bots_owner_id", table_name="bots")
    op.drop_table("bots")

    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
