class Calc():
    def __init__(self, number=0):
        self.number = {"test": number}

    def add(self, value):
        self.number["test"] = self.number["test"] + value
        return self

    def subtract(self, value):
        self.number["test"] = self.number["test"] - value
        return self


calc = Calc()

print(Calc().add(5).subtract(2).add(5).number)
# print(calc.number)  # 👉️ 8

print(Calc().subtract(5).add(3).number)
# print(calc.number)  # 👉️ 6
