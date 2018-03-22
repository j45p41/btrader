import datetime
import time
import os.path
import sys
import backtrader as bt
import backtrader.feeds as btfeed
import ccxt
import pandas as pd


# CSV INPUT FILE FORMAT CONFIGURATION
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

# MAIN STRATEGY DEFINITION
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
                self.buy(size=10)
        else:
            if self.rsi > self.params.rsi_high:
                self.sell(size=10)

# INPUT CONDITIONS TO FEED INTO CEREBRO IS ADDED HERE
if __name__ == '__main__':
    # Variable for our starting cash
    startcash = 10000
    # Create an instance of cerebro
    cerebro = bt.Cerebro(optreturn=False)

    # Timing the whole operation
    time_at_start = time.time()

    # ADD STRATEGY
    cerebro.optstrategy(firstStrategy, period=range(10, 20), rsi_low=range(10, 20), rsi_high=range(60, 70))

    # DATA FEED FROM EXCHANGE
    symbol = str('ETH/USDT')
    timeframe = str('15m')
    exchange = str('poloniex')
    exchange_out = str(exchange)
    start_date = str('2018-3-10 00:00:00')
    end_date = str('2018-3-16 19:00:00')
    get_data = False

    # Get our Exchange
    exchange = getattr(ccxt, exchange)()
    exchange.load_markets()


    def to_unix_time(timestamp):
        epoch = datetime.datetime.utcfromtimestamp(0)  # start of epoch time
        my_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")  # plugin your time object
        delta = my_time - epoch
        return delta.total_seconds() * 1000

    # CSV File Name
    symbol_out = symbol.replace("/", "")
    filename = '{}-{}-{}.csv'.format(exchange_out, symbol_out, timeframe)


    # Get data if needed

    if get_data == True:
        hist_start_date = int(to_unix_time(start_date))
        hist_end_date = int(to_unix_time(end_date))
        data = exchange.fetch_ohlcv(symbol, timeframe, since=hist_start_date, limit=hist_end_date)
        header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(data, columns=header)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')

        #Precision
        df = df.round(3)

        # Save it
        df.to_csv(filename, index= False)

    #READ DATA FROM CSV FILE
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath,str(filename))
    data = dataFeed(dataname=datapath, timeframe=bt.TimeFrame.Minutes, compression=15,)

    # Add the data to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(startcash)

    # RUN STRATEGY THROUGH CEREBRO USING INPUT DATA
    # Timing the operation
    time_at_end = time.time()
    time_elapsed = time_at_end - time_at_start
    print('Time elapsed: {} seconds'.format(time_elapsed))
    print ('Running Cerebro')
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

    # PRINT RESULTS
    result_number = 0
    print('Results: Ordered by Profit:')
    for result in by_PnL:
        if result_number < 3:
            print('Period: {}, rsi_low: {}, rsi_high: {}, PnL: {}'.format(result[0], result[1], result[2], result[3]))
            result_number = result_number + 1

    # Timing the operation
    time_at_end = time.time()
    time_elapsed = time_at_end - time_at_start

    print('Time elapsed: {} seconds'.format(time_elapsed))
    # cerebro.plot(style='candlestick')
