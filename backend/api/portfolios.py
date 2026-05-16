import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.auth import get_current_user_from_header
from database import get_db
from models import Portfolio, User
from schemas import GeneratedHouse, InvestRequest, PortfolioCreate, PortfolioResponse
from sim.rent_estimator import get_rent

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


def _get_portfolio(portfolio_id: int, user: User, db: Session) -> Portfolio:
    p = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(user: User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    return db.query(Portfolio).filter(Portfolio.user_id == user.id).all()


@router.post("", response_model=PortfolioResponse, status_code=201)
def create_portfolio(body: PortfolioCreate, user: User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    p = Portfolio(
        user_id=user.id,
        name=body.name,
        life=body.life,
        length=body.life,
        loan_repay_rate=body.loan_repay_rate,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, user: User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    return _get_portfolio(portfolio_id, user, db)


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: int, user: User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    p = _get_portfolio(portfolio_id, user, db)
    db.delete(p)
    db.commit()


@router.post("/{portfolio_id}/invest")
def invest(portfolio_id: int, body: InvestRequest, user: User = Depends(get_current_user_from_header), db: Session = Depends(get_db)):
    p = _get_portfolio(portfolio_id, user, db)
    p.cash     += body.amount
    p.invested += body.amount
    db.commit()
    return {"cash": p.cash, "invested": p.invested}


@router.get("/{portfolio_id}/available-houses", response_model=list[GeneratedHouse])
def available_houses(
    portfolio_id: int,
    count: int = 4,
    user: User = Depends(get_current_user_from_header),
    db: Session = Depends(get_db),
):
    p = _get_portfolio(portfolio_id, user, db)
    inflation = p.inflation

    base_prices = [180_000, 220_000, 260_000, 300_000, 340_000, 380_000, 420_000, 480_000]
    houses = []
    for _ in range(count):
        raw_price    = random.choice(base_prices) * inflation
        price        = round(raw_price / 1_000) * 1_000
        rent, meta   = get_rent(price)
        down_payment = round(price * 0.2, -2)
        houses.append(GeneratedHouse(
            price=price,
            expected_rent=rent,
            down_payment=down_payment,
            loan_amount=round(price * 0.8, -2),
            metadata=meta,
        ))
    return houses
