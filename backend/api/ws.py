from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

import auth as auth_utils
from database import SessionLocal
from models import House as HouseModel, Loan as LoanModel, Portfolio as PortfolioModel, User
from sim import Portfolio, World
from sim.house import House
from sim.loan import Loan

router = APIRouter(tags=["websocket"])


# ── DB ↔ sim conversion ───────────────────────────────────────────────────────

def _load(db: Session, portfolio_id: int, user_id: int) -> tuple[PortfolioModel, Portfolio] | None:
    db_p = db.query(PortfolioModel).filter(
        PortfolioModel.id == portfolio_id,
        PortfolioModel.user_id == user_id,
    ).first()
    if not db_p:
        return None

    world = World()
    world.inflation = db_p.inflation

    p = Portfolio(name=db_p.name, world=world, life=db_p.life, loan_repay_rate=db_p.loan_repay_rate)
    p.cash                = db_p.cash
    p.invested            = db_p.invested
    p.reserved            = db_p.reserved
    p.length              = db_p.length
    p.auto_buy_threshold  = db_p.auto_buy_threshold
    p._next_house_id      = db_p.next_house_id
    p._next_loan_id       = db_p.next_loan_id

    for h in db_p.houses:
        house = House.__new__(House)
        house.id               = h.house_id
        house.price            = h.price
        house.value            = h.value
        house.appreciation_rate = h.appreciation_rate
        house.metadata         = h.metadata or {}
        p.houses.append(house)

    for l in db_p.loans:
        loan          = Loan.__new__(Loan)
        loan.id       = l.loan_id
        loan.amount   = l.amount
        loan.original = l.original
        loan.rate     = l.rate
        loan.years    = l.years
        p.loans.append(loan)

    return db_p, p


def _save(db: Session, db_p: PortfolioModel, p: Portfolio):
    db_p.cash                = p.cash
    db_p.invested            = p.invested
    db_p.reserved            = p.reserved
    db_p.life                = p.life
    db_p.inflation           = p.world.inflation
    db_p.loan_repay_rate     = p.loan_repay_rate
    db_p.auto_buy_threshold  = p.auto_buy_threshold
    db_p.next_house_id       = p._next_house_id
    db_p.next_loan_id        = p._next_loan_id
    db_p.month              += 1

    # Sync houses
    sim_ids = {h.id for h in p.houses}
    for db_house in list(db_p.houses):
        if db_house.house_id not in sim_ids:
            db.delete(db_house)
    existing = {h.house_id: h for h in db_p.houses}
    for h in p.houses:
        if h.id in existing:
            existing[h.id].value = h.value
        else:
            db.add(HouseModel(
                portfolio_id=db_p.id,
                house_id=h.id,
                price=h.price,
                value=h.value,
                appreciation_rate=h.appreciation_rate,
                metadata=h.metadata,
            ))

    # Sync loans
    loan_ids = {l.id for l in p.loans}
    for db_loan in list(db_p.loans):
        if db_loan.loan_id not in loan_ids:
            db.delete(db_loan)
    existing_loans = {l.loan_id: l for l in db_p.loans}
    for l in p.loans:
        if l.id in existing_loans:
            existing_loans[l.id].amount = l.amount
        else:
            db.add(LoanModel(
                portfolio_id=db_p.id,
                loan_id=l.id,
                amount=l.amount,
                original=l.original,
                rate=l.rate,
                years=l.years,
            ))

    db.commit()


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/{portfolio_id}")
async def ws_endpoint(websocket: WebSocket, portfolio_id: int, token: str = ""):
    user_id = auth_utils.decode_token(token, expected_type="access")
    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    db = SessionLocal()

    try:
        result = _load(db, portfolio_id, user_id)
        if not result:
            await websocket.send_json({"type": "error", "message": "Portfolio not found"})
            return

        db_p, p = result
        await websocket.send_json({"type": "connected", "state": p.to_dict(), "month": db_p.month})

        async for raw in websocket.iter_json():
            action = raw.get("action")

            if action == "step":
                events = p.step_month(db_p.month + 1)
                _save(db, db_p, p)
                for event in events:
                    await websocket.send_json(event)

            elif action == "buy_house":
                price  = float(raw.get("price", 0))
                events = p.buy_house(price)
                _save(db, db_p, p)
                for event in events:
                    await websocket.send_json(event)
                await websocket.send_json({"type": "state_update", "state": p.to_dict()})

            elif action == "sell_house":
                house_id = int(raw.get("house_id", 0))
                events   = p.sell_house(house_id)
                _save(db, db_p, p)
                for event in events:
                    await websocket.send_json(event)
                await websocket.send_json({"type": "state_update", "state": p.to_dict()})

            elif action == "invest":
                amount = float(raw.get("amount", 0))
                event  = p.invest(amount)
                _save(db, db_p, p)
                await websocket.send_json(event)
                await websocket.send_json({"type": "state_update", "state": p.to_dict()})

            elif action == "update_settings":
                if "loan_repay_rate" in raw:
                    p.loan_repay_rate = float(raw["loan_repay_rate"])
                if "reserved" in raw:
                    p.reserved = float(raw["reserved"])
                if "auto_buy_threshold" in raw:
                    val = raw["auto_buy_threshold"]
                    p.auto_buy_threshold = float(val) if val is not None else None
                _save(db, db_p, p)
                await websocket.send_json({"type": "settings_updated", "state": p.to_dict()})

            elif action == "get_state":
                await websocket.send_json({"type": "state_update", "state": p.to_dict(), "month": db_p.month})

    except WebSocketDisconnect:
        pass
    finally:
        db.close()
