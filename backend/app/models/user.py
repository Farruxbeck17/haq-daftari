from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("sms_balance >= 0", name="ck_users_sms_balance"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    username = Column(String(255))
    phone_number = Column(String(32))
    preferred_currency = Column(String(3), nullable=False, default="UZS", server_default="UZS")
    sms_balance = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_transactions = relationship("DebtTransaction", foreign_keys="DebtTransaction.creator_id",
                                        back_populates="creator", passive_deletes=True)
    shared_transactions = relationship("DebtTransaction", foreign_keys="DebtTransaction.counterparty_id",
                                       back_populates="counterparty", passive_deletes=True)
