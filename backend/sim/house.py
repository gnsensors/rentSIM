from .rent_estimator import get_rent


class House:
    def __init__(self, id: int, price: float, appreciation_rate: float = 0.0021, sample_rent: bool = True):
        self.id = id
        self.price = price
        self.value = price
        self.appreciation_rate = appreciation_rate
        if sample_rent:
            _, self.metadata = get_rent(price)
        else:
            self.metadata = {}

    def monthly_expenses(self) -> float:
        # property tax (county + city) + insurance + maintenance, annualized / 12
        return ((0.0064 + 0.0016 + 0.0048 + 0.01) * self.value) / 12

    def pass_month(self) -> tuple[float, list[dict]]:
        events = []
        self.value *= 1 + self.appreciation_rate
        events.append({"type": "house_appreciated", "house_id": self.id, "value": round(self.value, 2)})

        rent, _ = get_rent(self.value)
        events.append({"type": "rent_collected", "house_id": self.id, "amount": rent})

        expenses = self.monthly_expenses()
        events.append({"type": "house_expenses", "house_id": self.id, "amount": round(expenses, 2)})

        return rent - expenses, events

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "price": round(self.price, 2),
            "value": round(self.value, 2),
            "appreciation_rate": self.appreciation_rate,
            "metadata": self.metadata,
            "monthly_expenses": round(self.monthly_expenses(), 2),
        }
