import datetime
import time
import os.path
import sys
import backtrader as bt
import backtrader.feeds as btfeed
#import ccxt
import csv
import io
import pandas as pd
from collections import OrderedDict
from multiprocessing import Pool, cpu_count
import math
import os


# DECLARE MODE FOR PROGRAM - OPTOMISATION OR STRATEGY
opt_mode = True

# LOG OUTPUT TO FILE
class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass

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
class OrderObserver(bt.observer.Observer):
    lines = ('created', 'expired',)

    plotinfo = dict(plot=True, subplot=True, plotlinelabels=True)

    plotlines = dict(
        created=dict(marker='*', markersize=8.0, color='lime', fillstyle='full'),
        expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full')
    )

    def next(self):
        for order in self._owner._orderspending:
            if order.data is not self.data:
                continue

            if not order.isbuy():
                continue

            # Only interested in "buy" orders, because the sell orders
            # in the strategy are Market orders and will be immediately
            # executed

            if order.status in [bt.Order.Accepted, bt.Order.Submitted]:
                self.lines.created[0] = order.created.price

            elif order.status in [bt.Order.Expired]:
                self.lines.expired[0] = order.created.price

# MAIN STRATEGY DEFINITION - DEFINE VALUES HERE FOR NON-OPTOMISATION MODE
class firstStrategy(bt.Strategy):
    params = (
        ("period", 11),
        ("rsi_low", 45),
        ("rsi_high", 63),
    )

    #TRADE LOGGING FUNCTION
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        if not opt_mode:
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.params.period)

    #TRADE LOGGING FUNCTION
    def notify_trade(self, trade):
        if not trade.isclosed and not opt_mode:
            return

        self.log('TRADE INFO, PRICE  %.2f, GROSS %.2f, NET %.2f' %
                 (trade.price, trade.pnl, trade.pnlcomm))
    def next(self):
        if not self.position:
            if self.rsi < self.params.rsi_low:
                self.buy(size=10)
        else:
            if self.rsi > self.params.rsi_high:
                self.sell(size=10)

if opt_mode == False:
    def printTradeAnalysis(analyzer):
        '''
        Function to print the Technical Analysis results in a nice format.
        '''
        #Get the results we are interested in
        total_open = analyzer.total.open
        total_closed = analyzer.total.closed
        total_won = analyzer.won.total
        total_lost = analyzer.lost.total
        win_streak = analyzer.streak.won.longest
        lose_streak = analyzer.streak.lost.longest
        pnl_net = round(analyzer.pnl.net.total,2)
        strike_rate = round((total_won / total_closed) * 100,2)
        #Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate','Win Streak', 'Losing Streak', 'PnL Net']
        r1 = [total_open, total_closed,total_won,total_lost]
        r2 = [strike_rate, win_streak, lose_streak, pnl_net]
        #Check which set of headers is the longest.
        if len(h1) > len(h2):
            header_length = len(h1)
        else:
            header_length = len(h2)
        #Print the rows
        print_list = [h1,r1,h2,r2]
        row_format ="{:<15}" * (header_length + 1)
        print("Trade Analysis Results:")
        for row in print_list:
            print(row_format.format('',*row))

    def printSQN(analyzer):
        sqn = round(analyzer.sqn,2)
        print('SQN: {}'.format(sqn))

# INPUT CONDITIONS TO FEED INTO CEREBRO IS ADDED HERE
if __name__ == '__main__':

    sys.stdout = Logger("firststrategy.log")


    periods = pd.DataFrame(columns=['FROM','TO'],index=[1,2,3])
    periods.loc[1] = ('2017-01-01','2017-02-01')
    periods.loc[2] = ('2017-02-01','2017-03-01')
    periods.loc[3] = ('2017-03-01','2017-04-01')


    for index, row in periods.iterrows():


        # Variable for our starting cash
        startcash = 10000
        # Create an instance of cerebro
        cerebro = bt.Cerebro(optreturn=False)

        # Timing the whole operation
        time_at_start = time.time()

        if opt_mode:
            # ADD STRATEGY OPTIMISATION
            #cerebro.optstrategy(firstStrategy, period=range(11, 20), rsi_low=range(10, 50), rsi_high=range(50, 90))
            cerebro.optstrategy(firstStrategy, period=range(10, 20), rsi_low=range(25, 50), rsi_high=range(55, 80))
        else:
            #ADD STRATEGY
            cerebro.addstrategy(firstStrategy)

        # DATA FEED FROM EXCHANGE
        symbol = str('ETH/USDT')
        timeframe = str('15m')
        exchange = str('poloniex')
        exchange_out = str(exchange)
        start_date = str('2017-1-1 00:00:00')
        get_data = False

        #So, let's say, you are fetching 2 days of 5m timeframe:
        #(1440 minutes in one day * 7 days) / 15 minutes = 576 candles

        num_of_candles = 672

        def to_unix_time(timestamp):
            epoch = datetime.datetime.utcfromtimestamp(0)  # start of epoch time
            my_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")  # plugin your time object
            delta = my_time - epoch
            return delta.total_seconds() * 1000

        # CSV File Name
        symbol_out = symbol.replace("/", "")
        filename = '{}-{}-{}.csv'.format(exchange_out, symbol_out, timeframe)
        out_filename = '{}-{}-{}-out.csv'.format(exchange_out, symbol_out, timeframe)


        # Get data if needed

        if get_data:
            # Get our Exchange
            exchange = getattr(ccxt, exchange)()
            exchange.load_markets()
            hist_start_date = int(to_unix_time(start_date))
            #data = exchange.fetch_ohlcv(symbol, timeframe, since=hist_start_date, limit=num_of_candles)
            data = exchange.fetch_ohlcv(symbol, timeframe, since=hist_start_date)
            header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = pd.DataFrame(data, columns=header)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')

            #Precision
            df = df.round(3)

            # Save it
            df.to_csv(filename, index= False)

        #format dates for datafeed object
        fy,fm,fd = periods['FROM'][index].split('-')
        ty,tm,td = periods['TO'][index].split('-')


#READ DATA FROM CSV FILE
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath,str(filename))
        data = dataFeed(dataname=datapath, timeframe=bt.TimeFrame.Minutes, compression=15,
                        fromdate=datetime.datetime(int(fy),int(fm),int(fd)),
                        todate=datetime.datetime(int(ty),int(tm),int(td)),)

        # Add the data to Cerebro
        cerebro.adddata(data)

        # Set our desired cash start
        cerebro.broker.setcash(startcash)

        if not opt_mode:
            # Add the analyzers we are interested in
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
            cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")


        #WRITER TEST
        #cerebro.addwriter(bt.WriterFile, csv=True, rounding=2)

        # RUN STRATEGY THROUGH CEREBRO USING INPUT DATA
        # Timing the operation
        time_at_end = time.time()
        time_elapsed = round(time_at_end - time_at_start,2)
        print('Time elapsed: {} seconds'.format(time_elapsed))
        print ('Running Cerebro')
        opt_runs = cerebro.run(tradehistory=False)
        firstStrat = opt_runs[0]


        if opt_mode:
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

            # PRINT RESULTS IN OPTIMISATION AND FILTER TOP 3
            result_number = 0
            print('Results: Ordered by Profit:')
            for result in by_PnL:
                if result_number < 3:
                    print('Asset: {} Start: {}, End: {}, Period: {}, rsi_low: {}, rsi_high: {}, PnL: {}'.format(filename, periods['FROM'][index], periods['TO'][index], result[0], result[1], result[2], result[3]))
                    result_number = result_number + 1

        # Timing the operation
        time_at_end = time.time()
        time_elapsed = round(time_at_end - time_at_start,2)


        print('Time elapsed: {} seconds'.format(time_elapsed))
        if opt_mode == False:
            # print the analyzers
            printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
            printSQN(firstStrat.analyzers.sqn.get_analysis())

            #Get final portfolio Value
            portvalue = cerebro.broker.getvalue()

            #Print out the final result
            print('Final Portfolio Value: ${}'.format(portvalue))
            #cerebro.plot(style='candlestick')
