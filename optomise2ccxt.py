import backtrader as bt
import ccxt
import datetime
import backtrader.feeds as btfeed
import math
import pandas as pd
import os.path
import sys

class dataFeed(btfeed.GenericCSVData):
    params = (
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1)
    )

class firstStrategy(bt.Strategy):
    params = (
        ("period", 21),
        ("rsi_low", 41),
        ("rsi_high", 66),
    )


    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.params.period)

    def next(self):
        if not self.position:
            if self.rsi < self.params.rsi_low:
                self.buy(size=100)
        else:
            if self.rsi > self.params.rsi_high:
                self.sell(size=100)

# INPUT CONDITIONS TO FEED INTO CEREBRO IS ADDED HERE
if __name__ == '__main__':
    # Variable for our starting cash
    startcash = 10000
    # Create an instance of cerebro
    cerebro = bt.Cerebro(optreturn=False)

    # Add our strategy
    cerebro.optstrategy(firstStrategy, period=range(14, 15), rsi_low=range(30, 40), rsi_high=range(55, 75))

    # DATA FEED FROM EXCHANGE

    symbol = str('ETH/USDT')
    timeframe = str('15m')
    exchange = str('poloniex')
    exchange_out = str(exchange)
    start_date = '2018,1,16'
    end_date = '2018,1,17'


    def to_unix_time(timestamp):
        epoch = datetime.datetime.utcfromtimestamp(0)  # start of epoch time
        my_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")  # plugin your time object
        delta = my_time - epoch
        return delta.total_seconds() * 1000.0

    hist_start_date = to_unix_time('2018-01-16 19:00:00')
    hist_end_date = to_unix_time('2018-01-17 19:00:00')

    # Get our Exchange
    exchange = getattr(ccxt, exchange)()
    exchange.load_markets()

    # Get data
    data = exchange.fetch_ohlcv(symbol, timeframe, since=hist_start_date, limit=hist_end_date)
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame(data, columns=header)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    #df = pd.DataFrame(data, columns=header).set_index('Timestamp')

    # Save it
    symbol_out = symbol.replace("/", "")
    filename = '{}-{}-{}.csv'.format(exchange_out, symbol_out, timeframe)
    df.to_csv(filename, index= False)

    #READ DATA FROM CSV FILE
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath,str(filename))
    data = dataFeed(dataname=datapath, timeframe=bt.TimeFrame.Minutes,compression=60)


    # Add the data to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(startcash)

    # RUN STRATEGY THROUGH CEREBRO USING INPUT DATA
    opt_runs = cerebro.run()

    # CREATE A LIST VARIABLE THAT CONTAINS RESULTS
    final_results_list = []
    for run in opt_runs:
        for strategy in run:
            value = round(strategy.broker.get_value(), 2)
            PnL = round(value - startcash, 2)
            period = strategy.params.period
            rsi_low = strategy.params.rsi_low
            rsi_high = strategy.params.rsi_high
            final_results_list.append([period, rsi_low, rsi_high, PnL])

    # Sort Results List
    by_period = sorted(final_results_list, key=lambda x: x[0])
    by_PnL = sorted(final_results_list, key=lambda x: x[3], reverse=True)

    # Print results
    #print('Results: Ordered by period:')
    #for result in by_period:
        #print('Period: {}, rsi_low: {}, rsi_high: {}, PnL: {}'.format(result[0], result[1], result[3], result[4]))
    print('Results: Ordered by Profit:')
    for result in by_PnL:
        print('Period: {}, rsi_low: {}, rsi_high: {}, PnL: {}'.format(result[0], result[1], result[2], result[3]))
