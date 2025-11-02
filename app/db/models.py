from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    marzban_username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    
    tariff_code: Mapped[str] = mapped_column(String(10))
    
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    data_limit_gb: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")

    invoice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)             
    vpn_link: Mapped[str | None] = mapped_column(String(500), nullable=True)   

    def __repr__(self):
        return f"<Subscription id={self.id} marzban_user={self.marzban_username} status={self.status}>"

