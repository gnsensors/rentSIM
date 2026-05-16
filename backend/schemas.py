from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PortfolioCreate(BaseModel):
    name: str
    life: int = 120
    loan_repay_rate: float = 1.0


class PortfolioResponse(BaseModel):
    id: int
    name: str
    cash: float
    invested: float
    reserved: float
    loan_repay_rate: float
    life: int
    length: int
    inflation: float
    month: int
    auto_buy_threshold: Optional[float]
    is_closed: bool
    model_config = {"from_attributes": True}


class InvestRequest(BaseModel):
    amount: float


class GeneratedHouse(BaseModel):
    price: float
    expected_rent: int
    down_payment: float
    loan_amount: float
    metadata: dict
