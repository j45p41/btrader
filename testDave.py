import sys

from datetime import datetime, timedelta
import backtrader as bt

class TestStrategy(bt.Strategy):
    def next(self):
        for data in self.datas:
            print('---------------------------- NEXT ----------------------------------')
            print("1: Data Name:                            {}".format(data._name))
            print("2: Bar Num:                              {}".format(len(data)))
            print("3: Current date:                         {}".format(data.datetime.datetime()))
            print('4: Open:                                 {}'.format(data.open[0]))
            print('5: High:                                 {}'.format(data.high[0]))
            print('6: Low:                                  {}'.format(data.low[0]))
            print('7: Close:                                {}'.format(data.close[0]))
            print('8: Volume:                               {}'.format(data.volume[0]))
            print('--------------------------------------------------------------------')


# Create a cerebro
cerebro = bt.Cerebro()

# Create data feeds
hist_start_date = datetime.utcnow() - timedelta(minutes=3)
data_min = bt.feeds.CCXT(exchange="bitfinex2", symbol="BTC/USD", name="btc_usd_min",
                         timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
                         config={'rateLimit': 10000, 'enableRateLimit': True}) #, historical=True)
cerebro.adddata(data_min)
# Add the strategy
cerebro.addstrategy(TestStrategy)

# Run the strategy
cerebro.run()