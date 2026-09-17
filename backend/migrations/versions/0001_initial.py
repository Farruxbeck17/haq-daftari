"""Dastlabki hisob-kitob jadvallari."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255)),
        sa.Column("username", sa.String(255)),
        sa.Column("phone_number", sa.String(32)),
        sa.Column("preferred_currency", sa.String(3), nullable=False, server_default="UZS"),
        sa.Column("sms_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("sms_balance >= 0", name="ck_users_sms_balance"))
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)
    op.create_table("debt_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("creator_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("counterparty_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("counterparty_name", sa.String(255), nullable=False),
        sa.Column("counterparty_phone", sa.String(32)),
        sa.Column("type", sa.Enum("GIVEN", "TAKEN", name="transactiontype"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("remaining_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="UZS"),
        sa.Column("due_date", sa.Date()),
        sa.Column("status", sa.Enum("PENDING_CONFIRMATION", "ACTIVE", "PARTIALLY_PAID", "SETTLED", "REJECTED", name="transactionstatus"), nullable=False),
        sa.Column("confirmation_token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("last_reminder_sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_debt_amount"),
        sa.CheckConstraint("remaining_amount >= 0 AND remaining_amount <= amount", name="ck_debt_remaining"),
        sa.CheckConstraint("counterparty_id IS NULL OR counterparty_id <> creator_id", name="ck_debt_parties"),
        sa.CheckConstraint("currency = 'UZS'", name="ck_debt_currency"))
    op.create_index("ix_debt_transactions_confirmation_token", "debt_transactions", ["confirmation_token"], unique=True)
    op.create_index("ix_debt_creator_created", "debt_transactions", ["creator_id", "created_at"])
    op.create_index("ix_debt_counterparty", "debt_transactions", ["counterparty_id"])
    op.create_index("ix_debt_status_due", "debt_transactions", ["status", "due_date"])
    op.create_table("repayment_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("debt_transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("note", sa.Text()),
        sa.Column("recorded_by_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_repayment_amount"),
        sa.UniqueConstraint("transaction_id", "idempotency_key", name="uq_repayment_request"))
    op.create_index("ix_repayment_history_transaction_id", "repayment_history", ["transaction_id"])


def downgrade():
    op.drop_table("repayment_history")
    op.drop_table("debt_transactions")
    op.drop_table("users")
    postgresql.ENUM(name="transactionstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="transactiontype").drop(op.get_bind(), checkfirst=True)
