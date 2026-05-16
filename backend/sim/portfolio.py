from .world import World
from .house import House
from .loan import Loan
from .rent_estimator import get_rent


class Portfolio:
    def __init__(
        self,
        name: str,
        world: World,
        life: int = 120,
        loan_repay_rate: float = 1.0,
    ):
        self.name = name
        self.world = world
        self.life = life
        self.length = life
        self.loan_repay_rate = loan_repay_rate
        self.cash = 0.0
        self.invested = 0.0
        self.reserved = 0.0
        self.auto_buy_threshold: float | None = None
        self.houses: list[House] = []
        self.loans: list[Loan] = []
        self._next_house_id = 1
        self._next_loan_id = 1

    # ── Actions ───────────────────────────────────────────────────────────────

    def invest(self, amount: float) -> dict:
        self.cash += amount
        self.invested += amount
        return {"type": "invested", "amount": round(amount, 2), "total_cash": round(self.cash, 2)}

    def take_loan(self, amount: float, rate: float = 0.06, years: float = None, cash_advance: bool = True) -> tuple[Loan, dict]:
        if years is None:
            years = self.life / 12
        loan = Loan(id=self._next_loan_id, amount=amount, rate=rate, years=years)
        self._next_loan_id += 1
        self.loans.append(loan)
        if cash_advance:
            self.cash += amount
        return loan, {
            "type": "loan_taken",
            "loan_id": loan.id,
            "amount": round(amount, 2),
            "rate": rate,
            "years": years,
            "monthly_payment": round(loan.monthly_payment, 2),
        }

    def buy_house(self, price: float, appreciation_rate: float = 0.0021, down: float = 0.2) -> list[dict]:
        full_price   = price * self.world.inflation
        down_payment = full_price * down
        loan_amount  = full_price * (1 - down)

        if (self.cash - self.reserved) < down_payment:
            return [{"type": "buy_failed", "reason": "insufficient_cash", "price": round(full_price, 2)}]

        self.cash -= down_payment
        house = House(id=self._next_house_id, price=full_price, appreciation_rate=appreciation_rate)
        self._next_house_id += 1
        self.houses.append(house)
        events = [{"type": "house_bought", "house_id": house.id, "price": round(full_price, 2), "down_payment": round(down_payment, 2)}]

        if loan_amount > 0:
            _, loan_event = self.take_loan(loan_amount, cash_advance=False)
            events.append(loan_event)

        return events

    def sell_house(self, house_id: int) -> list[dict]:
        house = next((h for h in self.houses if h.id == house_id), None)
        if not house:
            return [{"type": "sell_failed", "reason": "not_found", "house_id": house_id}]
        self.houses.remove(house)
        self.cash += house.value
        return [{"type": "house_sold", "house_id": house_id, "value": round(house.value, 2)}]

    # ── Monthly step ──────────────────────────────────────────────────────────

    def step_month(self, month: int) -> list[dict]:
        if self.life <= 0:
            return self._close()

        self.life -= 1
        events: list[dict] = []

        events.append(self.world.pass_month())

        # Collect rent and appreciate houses
        total_flow = 0.0
        for house in self.houses:
            net, house_events = house.pass_month()
            events.extend(house_events)
            total_flow += net
            self.cash += net

        events.append({"type": "total_flow", "amount": round(total_flow, 2)})

        if round(self.cash) < 0:
            _, ev = self.take_loan(-self.cash, rate=0.18, years=1 / 12)
            events.append({**ev, "type": "emergency_loan"})
            self.cash = 0.0

        # Pay loans — largest balance first, extra cash toward payoff
        if self.loans:
            base_total = sum(l.monthly_payment for l in self.loans)
            self.loans.sort(key=lambda l: l.amount, reverse=True)
            paid_off = []
            for loan in self.loans:
                if self.cash >= base_total:
                    extra = max(0.0, (self.cash - self.reserved - base_total) * self.loan_repay_rate)
                    payment, ev = loan.pay(extra=extra)
                else:
                    payment, ev = loan.pay()
                base_total -= loan.monthly_payment
                self.cash -= payment
                if ev:
                    events.append(ev)
                if loan.amount <= 0:
                    paid_off.append(loan)
            for loan in paid_off:
                self.loans.remove(loan)

            if round(self.cash) < 0:
                _, ev = self.take_loan(-self.cash, rate=0.18, years=1 / 12)
                events.append({**ev, "type": "emergency_loan"})
                self.cash = 0.0

        # Auto-buy
        if self.auto_buy_threshold is not None:
            threshold = self.auto_buy_threshold * self.world.inflation
            if (self.cash - self.reserved) >= threshold:
                price = self.auto_buy_threshold / 0.2  # threshold is down payment target
                buy_events = self.buy_house(price)
                events.extend(buy_events)

        events.append({"type": "month_complete", "month": month, "state": self.to_dict()})
        return events

    def _close(self) -> list[dict]:
        events = []
        for house in self.houses:
            self.cash += house.value
            events.append({"type": "house_sold", "house_id": house.id, "value": round(house.value, 2), "reason": "close"})
        self.houses.clear()

        total_loans = sum(l.amount for l in self.loans)
        self.cash -= total_loans
        events.append({"type": "loans_settled", "total": round(total_loans, 2)})
        self.loans.clear()

        events.append({"type": "portfolio_closed", "final_cash": round(self.cash, 2), "net_gain": round(self.cash - self.invested, 2)})
        return events

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cash": round(self.cash, 2),
            "invested": round(self.invested, 2),
            "reserved": round(self.reserved, 2),
            "life_remaining": self.life,
            "length": self.length,
            "loan_repay_rate": self.loan_repay_rate,
            "auto_buy_threshold": self.auto_buy_threshold,
            "inflation": round(self.world.inflation, 6),
            "houses": [h.to_dict() for h in self.houses],
            "loans": [l.to_dict() for l in self.loans],
            "total_asset_value": round(sum(h.value for h in self.houses), 2),
            "total_loan_balance": round(sum(l.amount for l in self.loans), 2),
        }
