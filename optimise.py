import backtrader as bt
from datetime import datetime


class firstStrategy(bt.Strategy):
    params = (
        ('period', 21),
    )

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.params.period)

    def next(self):
        if not self.position:
            if self.rsi < 30:
                self.buy(size=100)
        else:
            if self.rsi > 70:
                self.sell(size=100)

    def stop(self):
        pnl = round(self.broker.getvalue() - self.startcash,2)
        print('RSI Period: {} Final PnL: {}'.format(
            self.params.period, pnl))

# Variable for our starting cash
startcash = 10000

# Create an instance of cerebro
cerebro = bt.Cerebro()

# Add our strategy
cerebro.optstrategy(firstStrategy, period=range(14, 21))

# Get Apple data from Yahoo Finance.
data = bt.feeds.YahooFinanceData(
    dataname='AAPL',
    fromdate=datetime(2016, 1, 1),
    todate=datetime(2017, 1, 1),
    buffered=True
)

# Add the data to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(startcash)

# Run over everything
cerebro.run()
