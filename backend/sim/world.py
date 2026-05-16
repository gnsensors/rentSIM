class World:
    def __init__(self, inflation_rate: float = 0.00205):
        self.inflation_rate = inflation_rate
        self.inflation = 1.0

    def pass_month(self) -> dict:
        self.inflation *= 1 + self.inflation_rate
        return {"type": "inflation_updated", "inflation": round(self.inflation, 6)}
