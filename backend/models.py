from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    email         = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id                 = Column(Integer, primary_key=True)
    user_id            = Column(Integer, ForeignKey("users.id"), nullable=False)
    name               = Column(String, nullable=False)
    cash               = Column(Float, default=0.0)
    invested           = Column(Float, default=0.0)
    reserved           = Column(Float, default=0.0)
    loan_repay_rate    = Column(Float, default=1.0)
    life               = Column(Integer, default=120)
    length             = Column(Integer, default=120)
    inflation          = Column(Float, default=1.0)
    month              = Column(Integer, default=0)
    auto_buy_threshold = Column(Float, nullable=True)
    is_closed          = Column(Boolean, default=False)
    next_house_id      = Column(Integer, default=1)
    next_loan_id       = Column(Integer, default=1)
    created_at         = Column(DateTime, default=datetime.utcnow)

    user   = relationship("User", back_populates="portfolios")
    houses = relationship("House", back_populates="portfolio", cascade="all, delete-orphan")
    loans  = relationship("Loan",  back_populates="portfolio", cascade="all, delete-orphan")


class House(Base):
    __tablename__ = "houses"

    id               = Column(Integer, primary_key=True)
    portfolio_id     = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    house_id         = Column(Integer, nullable=False)
    price            = Column(Float, nullable=False)
    value            = Column(Float, nullable=False)
    appreciation_rate = Column(Float, default=0.0021)
    metadata         = Column(JSON, default=dict)

    portfolio = relationship("Portfolio", back_populates="houses")


class Loan(Base):
    __tablename__ = "loans"

    id           = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    loan_id      = Column(Integer, nullable=False)
    amount       = Column(Float, nullable=False)
    original     = Column(Float, nullable=False)
    rate         = Column(Float, nullable=False)
    years        = Column(Float, nullable=False)

    portfolio = relationship("Portfolio", back_populates="loans")
