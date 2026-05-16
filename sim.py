import houses
import time
import sys

class World:
    def __init__(self, inflation_rate = 0.00205):
        self.inflation_rate = inflation_rate
        self.inflation = 1
    def pass_month(self):
        self.inflation *= 1 + self.inflation_rate
        print(f"World inflation: {self.inflation:.2f}x from start\n")

class Loan:
    def __init__(self, amount, rate, years):
        self.amount = amount
        self.rate = rate
        self.original = amount
        self.years = years
        self.monthly = self.calculate_monthly_payment()
    
    def calculate_monthly_payment(self):
        return self.amount * ((self.rate/12) * (1 + self.rate/12)**(12*self.years)) / ((1 + self.rate/12)**(12*self.years) - 1)

    def pay(self, extra = 0):
        if extra > 0:
            print(f"Paying extra ${extra:,.2f} towards a loan of ${self.amount:,.2f}")
        if self.amount <= 0:
            return 0
        self.monthly = self.calculate_monthly_payment()
        payment = min(self.monthly + extra, self.amount)
        self.amount -= payment
        return payment

class Portfolio:
    def __init__(self, name, world: World, life = 120, loan_repay_rate = 1):
        self.world = world
        self.loan_repay_rate = loan_repay_rate
        self.name = name
        self.houses = []
        self.cash = 0
        self.invested = 0
        self.reserved = 0
        self.loan_money = 0
        self.life = life
        self.length = life
        self.loans: list[Loan] = []
    
    def invest(self, amount):
        self.cash += amount
        self.invested += amount
        print(f"Invested ${amount:,.2f} into portfolio \"{self.name}\". Total current liquid portfolio value: ${self.cash:,.2f}\n")
    
    def reserve(self, amount):
        self.reserved += amount
        print(f"Reserved ${amount:,.2f} in portfolio \"{self.name}\". Total reserve: ${self.reserved:,.2f}\n")

    def loan(self, amount, rate = 0.06, months = None):
        if not months:
            months = self.life
        new_loan = Loan(amount, rate, months)
        self.loans.append(new_loan)
        self.cash += amount
        print(f"{self.name} took out a loan for ${amount:,.2f}. Monthly payment: ${new_loan.monthly:,.2f}")

    def step_month(self, month, purchase = False, down = 0.2):
        # Calculate protfolio life and close if necessary
        if self.life == 0:
            self.close()
            return
        self.life -= 1

        # Calculate net cash flow from houses and add to cash
        total_flow = 0
        for house in self.houses:
            flow = house.pass_month()
            total_flow += flow
            self.cash += flow
            print("")
        print(f"Total cash flow from houses: ${total_flow:,.2f}\n")

        if round(self.cash) < 0:
            print(f"Need to pay ${-round(self.cash):,.2f} in house payments")
            print(f"Portfolio \"{self.name}\" is in debt for ${-round(self.cash):,.2f}. Taking out a small loan to cover the deficit.")
            self.loan(-self.cash, rate=0.18, months=1)
            print(f"Paid ${-round(self.cash):,.2f} in house payments\n")
            self.cash = 0
        print(f"Current liquid portfolio value: ${self.cash:,.2f}\n")

        # Pay off loans and take out new ones if necessary
        if len(self.loans) > 0:
            loan_base_total = sum(loan.calculate_monthly_payment() for loan in self.loans)
            total_loans = 0
            self.loans.sort(key=lambda loan: loan.amount, reverse=True)
            for loan in self.loans:
                if self.cash >= loan_base_total:
                    loan_monthly = loan.pay(extra=((self.cash - self.reserved) - loan_base_total) * self.loan_repay_rate)
                    loan_base_total -= loan.calculate_monthly_payment()
                else:
                    loan_monthly = loan.pay()
                total_loans += loan_monthly
                self.cash -= loan_monthly
                if round(loan.amount) <= 0:
                    print(f"Loan originally for ${loan.original:,.2f} fully paid off and removed from portfolio \"{self.name}\"")
                    self.loans.remove(loan)
            use_plural = " " if len(self.loans) == 1 else "s"
            print(f"Need to pay ${total_loans:,.2f} for {len(self.loans)} loan{use_plural}")
            if round(self.cash) < 0:
                print(f"Portfolio \"{self.name}\" is in debt for ${-self.cash:,.2f}. Taking out a small loan to cover the deficit.")
                self.loan(-self.cash, rate=0.18, months=1)
                self.cash = 0
                print(f"Paid ${total_loans:,.2f} for {len(self.loans) - 1} loan{use_plural}\n")
            else:
                print(f"Paid ${total_loans:,.2f} for {len(self.loans)} loan{use_plural}\n")

        if purchase:
                if (self.cash - self.reserved) > purchase * self.world.inflation:
                    self.buy_house(self.world, (purchase * self.world.inflation) / down)

        print(f"End of month #{month} for portfolio \"{self.name}\".")
        print(f"    Current liquid value: ${self.cash:,.2f}")
        print(f"    Current asset value: ${sum(house.value for house in self.houses):,.2f}")
        print(f"    Current inflation: {self.world.inflation:.2f}x from start\n")

    def close(self):
        print(f"\n\nClosing portfolio \"{self.name}\"\n")
        for house in self.houses:
            print(f"Sold house #{house.id} for ${house.value:,.2f}")
            self.cash += house.value
        total_loans = sum(loan.amount for loan in self.loans)
        self.cash -= total_loans
        use_plural = " " if len(self.loans) == 1 else "s"
        print(f"Paid off {len(self.loans)} loan{use_plural} for a total of ${total_loans:,.2f}")
        print(f"Final net value for portfolio \"{self.name}\": ${self.cash:,.2f}")
        self.cash -= self.invested
        print(f"Final net gain for portfolio \"{self.name}\": ${self.cash:,.2f}")
        print(f"Adjusted profit for inflation: ${((self.cash + self.invested) / self.world.inflation) - self.invested:,.2f}")
        print(f"Adjusted & relative to investment: ${(((self.cash + self.invested) / self.world.inflation)) / self.invested:,.2f}x")
        print(f"Adjusted annual return: ${((((self.cash + self.invested) / self.world.inflation) - self.invested) / self.length) * 12:,.2f}")
        cd4revenue = self.invested * (1.04 ** (self.length / 12))
        print(f"4% CD profit: ${cd4revenue - self.invested:,.2f}")
        print(f"4% CD profit adjusted for inflation: ${cd4revenue / self.world.inflation - self.invested:,.2f}")
        print(f"4% CD adjusted & relative to investment: {(cd4revenue / self.world.inflation) / self.invested:,.2f}x")
        print(f"Real estate advantage: ${(self.cash) - (cd4revenue):,.2f}")
        print(f"Adjusted real estate advantage: ${((self.cash + self.invested) / self.world.inflation) - (cd4revenue / self.world.inflation):,.2f}")
        print(f"Adjusted & relative real estate advantage: {((self.cash / self.world.inflation) - self.invested) / ((cd4revenue / self.world.inflation) - self.invested):,.2f}x")

    def buy_house(self, world: World, price, appreciation_rate = 0.00201):
        price = price * world.inflation
        if (self.cash - self.reserved) < price:
            self.loan(price - (self.cash - self.reserved))
            self.cash -= price
            self.houses.append(House(len(self.houses) + 1, world, price, appreciation_rate))
            print(f"House #{len(self.houses)} bought for portfolio \"{self.name}\". Current liquid portfolio value: ${self.cash:,.2f}\n")  
            return
        self.cash -= price
        self.houses.append(House(len(self.houses) + 1, world, price, appreciation_rate))
        print(f"House #{len(self.houses)} bought for portfolio \"{self.name}\". Current liquid portfolio value: ${self.cash:,.2f}\n")        

    def process(self, auto = 0, purchase = False, down = 0.2):
        for i in range(p1.life + 1):
            if auto == True:
                pass
            elif auto == False:
                input("Press Enter to continue to next month... ")
            else:
                time.sleep(auto)
                
            if i < self.life:
                print(f"\n\nStarting month {i+1}")
            world.pass_month()
            p1.step_month(i+1, purchase, down)

class House:
    def __init__(self, id, world: World, price, appreciation_rate = 0.0021):
        self.id = id
        self.world = world
        self.price = price
        self.appreciation_rate = appreciation_rate
        self.value = price
        initial_rent = houses.get_rent(self.value)[0]
        expenses = self.standard_expenses()

        print(f"House #{self.id} bought for: ${self.value:,.2f}")
        print(f"House #{self.id}'s monthly expenses: ${expenses:,.2f}")
        print(f"House #{self.id}'s initial rent: ${initial_rent:,.2f}")
        print(f"House #{self.id}'s base net gain: ${initial_rent - expenses:,.2f}")
        
    def appreciate(self):
        self.value *= (1 + self.appreciation_rate)

    def standard_expenses(self):
        county = 0.0064 * self.value
        city = 0.0016 * self.value
        insurance = 0.0048 * self.value
        maintenance = 0.01 * self.value
        return (county + city + insurance + maintenance) / 12 # Yearly expenses divided by 12 for monthly
    
    def rent(self):
        rent = houses.get_rent(self.value)[0]
        print(f"Rent collected from house #{self.id}: ${rent:,.2f}")
        return rent
    
    def pass_month(self):
        net = 0
        self.appreciate()
        net += self.rent()
        expenses = self.standard_expenses()
        net -= expenses
        print(f"House #{self.id}'s monthly expenses: ${expenses:,.2f}")
        print(f"Net liquid cash flow from house #{self.id}: ${net:,.2f}")
        print(f"House #{self.id}'s value: ${self.value:,.2f}")
        return net

def progress_bar(duration):
    total_length = 30
    start = time.time()

    print("CALCULATING")

    while True:
        elapsed = time.time() - start
        if elapsed > duration:
            elapsed = duration

        progress = elapsed / duration
        filled = int(total_length * progress)
        bar = "#" * filled + "-" * (total_length - filled)

        percent = int(progress * 100)
        remaining = int(duration - elapsed)

        sys.stdout.write(
            f"\r[{bar}] {percent}% done, Elapsed: {int(elapsed)}s, Remaining: {remaining}s"
        )
        sys.stdout.flush()

        if elapsed >= duration:
            break

        time.sleep(0.1)

    print("\n")

if __name__ == "__main__":
    print("\n\nWelcome to the real estate investment simulator!\n\n\n")
    world  = World()
    p1 = Portfolio("Henry's Get Rich Slow Scheme", world, 360)
    p1.invest(500_000)
    p1.reserve(20_000)
    p1.loan_repay_rate = 0.5
    progress_bar(p1.life * 0.02)
    p1.process(True, purchase=80_000, down=0.2)