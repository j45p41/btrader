import time
import configparser
import sys

from datetime import datetime, timedelta

import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds

from pandas import bdate_range


class GeminiBTC200MAH1Strategy(bt.Strategy):

    def __init__(self):

        self.sma200 = btind.SimpleMovingAverage(self.data, period=200)

    def next(self):
        for data in self.datas:
            print('*' * 5, 'NEXT:', bt.num2date(data.datetime[0]), data._name, data.open[0], data.high[0],
                  data.low[0], data.close[0], data.volume[0],
                  bt.TimeFrame.getname(data._timeframe), len(data))
            if not self.getposition(data) and data.close[0] > self.sma200[0]:
                order = self.buy(data, exectype=bt.Order.Market, size=10)
            elif self.getposition(data) and data.close[0] < self.sma200[0]:
                order = self.sell(data, exectype=bt.Order.Market, size=10)

    def notify_order(self, order):
        print('*' * 5, "NOTIFY ORDER", order)


def runstrategy(argv):
    # Create a cerebro
    cerebro = bt.Cerebro()



    # Create data feeds
    hist_start_date = bdate_range(end=(datetime.now() - timedelta(days=10)), periods=1)[0].to_pydatetime()
    # hist_start_date = datetime.utcnow() - timedelta(minutes=30)
    data_hour = bt.feeds.CCXT(exchange="gdax", symbol="BTC/USD", name="btc_usd_1h", timeframe=bt.TimeFrame.Minutes,
                              compression=60, fromdate=hist_start_date)
    cerebro.adddata(data_hour)

    # Add the strategy
    cerebro.addstrategy(GeminiBTC200MAH1Strategy)

    # Run the strategy
    cerebro.run(stdstats=False)


if __name__ == '__main__':
    sys.exit(runstrategy(sys.argv))