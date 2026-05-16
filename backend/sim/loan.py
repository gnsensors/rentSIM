class Loan:
    def __init__(self, id: int, amount: float, rate: float, years: float):
        self.id = id
        self.amount = amount
        self.original = amount
        self.rate = rate
        self.years = years

    @property
    def monthly_payment(self) -> float:
        r = self.rate / 12
        n = 12 * self.years
        if self.amount <= 0 or n == 0:
            return 0.0
        if r == 0:
            return self.amount / n
        return self.amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def pay(self, extra: float = 0) -> tuple[float, dict]:
        if self.amount <= 0:
            return 0.0, None
        payment = min(self.monthly_payment + extra, self.amount)
        self.amount -= payment
        if round(self.amount, 2) <= 0:
            self.amount = 0.0
            return payment, {
                "type": "loan_paid_off",
                "loan_id": self.id,
                "original": round(self.original, 2),
            }
        return payment, {
            "type": "loan_payment",
            "loan_id": self.id,
            "amount": round(payment, 2),
            "remaining": round(self.amount, 2),
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": round(self.amount, 2),
            "original": round(self.original, 2),
            "rate": self.rate,
            "years": self.years,
            "monthly_payment": round(self.monthly_payment, 2),
        }
