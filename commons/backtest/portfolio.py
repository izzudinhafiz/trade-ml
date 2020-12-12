import inspect
from datetime import datetime, timedelta
from commons.helper import get_caller
from pprint import pprint
from commons.money import Money


class Portfolio:
    def __init__(self, start_value: float = None, start_date: datetime = None, end_date: datetime = None):
        self.cash = Money(start_value)
        self.equity = Money(start_value)
        self.positions = []
        self.market = get_caller(inspect.stack()[1][0])
        self.start_date = start_date if start_date is not None else self.market.start_date
        self.end_date = end_date if end_date is not None else self.market.end_date
        self.margin = start_value

    def open_position_by_value(self, symbol, value):
        if self.can_open(value):
            self.process_open(Position.open_by_value(symbol, value))
            return True
        return False

    def open_position_by_size(self, symbol, size):
        current_price = self.market.get_current_price(symbol)
        buy_value = current_price * size
        if self.can_open(buy_value):
            self.process_open(Position.open_by_value(symbol, buy_value))
            return True
        return False

    def open_position_by_ratio(self, symbol, ratio):
        if ratio > 0:
            buy_value = self.cash * ratio
        elif ratio < 0:
            buy_value = self.margin * ratio
        else:
            return False
        if self.can_open(buy_value):
            self.process_open(Position.open_by_value(symbol, buy_value))
            return True
        return False

    def can_open(self, value):
        if type(value) != Money:
            value = Money(value)

        if value > 0:
            if self.cash < value:
                return False
        else:
            if self.margin < value:
                return False

        return True

    def process_open(self, position):
        if position.position_type == "long":
            self.cash -= position.open_value
            self.equity += position.nett_gain
        elif position.position_type == "short":
            self.cash += position.open_value
            self.equity += position.nett_gain
        else:
            raise AttributeError(f"Position type is {position.position_type}. Invalid type")
        self.positions.append(position)

    def process_close(self, position):
        pass

    def update(self):
        total_value = 0
        for position in self.positions:
            total_value += position.current_value

        self.equity = total_value
        self.score_stock()
        self.optimizer()
        self.execute()

    def optimizer(self):
        pass

    def score_stock(self):
        pass

    def execute(self):
        pass

    def end_simulation(self):
        pass


class Position:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.symbol = None
        self.size = None
        self.position_type = None
        self.active = None

        self.open_price = None
        self.open_value = None
        self.open_time = None
        self.open_commission = Money(0)

        self.current_value = None
        self.current_price = None

        self.close_value = None
        self.close_time = None
        self.close_price = None
        self.close_commission = Money(0)

        self.nett_gain = None
        self.commission_rate = 0.01
        self.total_commission = self.open_commission + self.close_commission

    @classmethod
    def open_by_value(cls, symbol, value):
        if type(value) != Money:
            value = Money(value)
        position = cls(get_caller(inspect.stack()[1][0]))  # get_caller gets the portfolio object that called this position.
        market = position.portfolio.market
        current_price = market.get_current_price(symbol)
        size = value / current_price
        position.open_position(symbol, size, current_price)

        return position

    def open_position(self, symbol: str, size: Money, open_price: Money):
        self.symbol = symbol
        self.size = size
        self.open_price = Money(open_price)
        self.current_price = Money(open_price)
        self.open_value = self.open_price * self.size
        self.current_value = self.current_price * self.size
        self.open_time = self.portfolio.market.time_now
        self.active = True
        self.position_type = "long" if size > 0 else "short"
        self.open_commission = Money(self.open_value * self.commission_rate)
        self.total_commission = self.open_commission
        self.calculate_nett_gain()

        return self.current_value

    def close_position(self):
        self.close_time = self.portfolio.market.time_now
        self.close_price = self.portfolio.market.get_current_price(self.symbol)
        self.current_price = self.close_price
        self.close_value = self.close_price * self.size
        self.close_commission = round(self.commission_rate * self.close_value, 2)
        self.total_commission = self.open_commission + self.close_commission
        self.active = False
        self.calculate_nett_gain()

        return (self.close_value, self.nett_gain)

    def calculate_nett_gain(self):
        if self.position_type == "long":
            gross_gain = self.current_value - self.open_value
            self.nett_gain = gross_gain - self.total_commission
        elif self.position_type == "short":
            gross_gain = self.open_value - self.current_value
            self.nett_gain = gross_gain - self.total_commission

    def update(self):
        self.current_price = self.portfolio.market.get_current_price(self.symbol)
        self.current_value = self.current_price * self.size
        self.calculate_nett_gain()

        return self.nett_gain
