from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import argparse
import pandas as pd, numpy as np
import datetime
import ntpath
from scipy.stats import norm
# import matplotlib.pyplot as plt
# import matplotlib
# import matplotlib.dates as mdates
import operator
import math
import sys
import os
import scipy.optimize as spo
import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
import glob
import ntpath


def parse_args():
    parser = argparse.ArgumentParser(description='MultiData Strategy')

    parser.add_argument('--data0', '-d0',
                        default='C:/Users/Jaspal/OneDrive/Financial Stuff/btrader_git/poloniex-ETHUSDT-15m.csv',
                        help='Directory of CSV data source')

    parser.add_argument('--betaperiod',
                        default=1.4, type=float,
                        help='Per "Inside the Black Box" Mean. 1.4 also outperforms old model of 3months.')

    parser.add_argument('--fromdate', '-f',
                        default='2017-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2017-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--buyscore',
                        action='store',  # 0.91884558 #0.92 is best over 10 years..
                        default=0.91, type=float,
                        help=('Min BRM score for a buy'))

    parser.add_argument('--stoploss',
                        action='store',
                        default=0.05, type=float,
                        help=('sell a long position if loss exceeds'))

    parser.add_argument('--takeprofit',
                        action='store',
                        default=0.5, type=float,
                        help=('Exit a long position if profit exceeds'))

    parser.add_argument('--limitpct',
                        action='store',
                        default=0.03, type=float, #DEFAULT: 0.03 (gives good result)
                        help=('For buying at LIMIT, this will only purchase if the price is less than (1+limitpct)*Closing price'))

    parser.add_argument('--validdays',
                        action='store',
                        default=7, type=int,
                        help=('The number of days which a buy order remains valid'))

    parser.add_argument('--sellscore',
                        action='store',
                        default=-0.91, type=float,
                        help=('Max score for a sell'))

    parser.add_argument('--marketindex',
                        default='XJO',
                        help=('XAO = All Ords, XJO = ASX200'))

    parser.add_argument('--cash',
                        default=100000, type=int,
                        help='Starting Cash')

    parser.add_argument('--pctperstock',
                        action='store', #0.083 = 1/12... i.e. a portfolio of up to 12 stocks
                        default=0.083, type=float, #i.e. 10% portfolio value in each stock
                        help=('Pct of portfolio starting cash to invest in each stock purchase'))

    parser.add_argument('--mintrade',
                        default=1000, type=float,
                        help='Smallest dollar value to invest in a stock (if cash level below amount required for pctperstock)')

    parser.add_argument('--tradefee',
                        default=10.0, type=float,
                        help='CMC Markets Fee per stock trade (BUY OR SELL)')

    # **UNUSED** see BROKER COMMISSION which performs calculation based on purchase amount
    parser.add_argument('--commperc',
                        default=0.002, type=float,
                        help='Percentage commission for operation (0.005 is 0.5%%')

    parser.add_argument('--plot', '-p',
                        action='store_true',
                        default=True,
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n',
                        default=1, type=int,
                        help='Plot using numfigs figures')

    return parser.parse_args()

# Create a Strategy. Defn "Class": a logical grouping of data and functions (the later of which are frequently referred to as "methods" when defined within a class). Classes can be thought of as blueprints for creating objects. https://jeffknupp.com/blog/2014/06/18/improve-your-python-python-classes-and-object-oriented-programming/
class TestStrategy(bt.Strategy):
    # Attributes which apply to ALL instances of a Class object are defined here, i.e. prior to __init__
    args = parse_args()
    params = (
        ('printlog', True),
        ('prtrade', False),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function for this strategy'''
        if self.p.printlog or doprint:  # NB: self.p = self.params
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):  # __init__ = creates object defined by the Class. INITIALISES the object - sets all attributes
        self.order = {}
        self.order_sl = {}
        self.order_tp = {}
        self.bar_executed = {}
        for i, d in enumerate(d for d in self.datas):
            self.order[d._name] = None
            self.order_sl[d._name] = None
            self.order_tp[d._name] = None
            self.bar_executed[d._name] = None


        # Add a MovingAverageSimple indicator
        #self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.p.maperiod)
        # Plot Indicators if plot function called
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)


    def start(self):
        pass

    def notify_trade(self, trade):
        '''
        Receives a trade whenever there has been a change in one.  **TRADE = EXITED MARKET POSITION**
        Keeps track of the life of an trade: size, price, commission (and value?) An trade starts at 0 can be
        increased and reduced and can be considered closed if it goes back to 0.The trade can be long (positive size)
        or short (negative size) An trade is not meant to be reversed (no support in the logic for it)
        Note: "print(Trade.__dict__)" gives: {'barclose': 1226, 'justopened': False, 'status': 2, 'size': 0, 'data': <__main__.CustomDataLoader object at 0x0000027B9F0DA198>, 'price': 11.03, 'long': True, 'isclosed': True, 'pnl': 536.0500000000006, 'isopen': False, 'barlen': 6, 'ref': 605, 'historyon': False, 'commission': 20.712469879518075, 'baropen': 1220, 'tradeid': 0, 'dtclose': 736275.0, 'dtopen': 736265.0, 'pnlcomm': 515.3375301204826, 'history': [], 'value': 0.0}
        '''

        #MARKET POSITION EXITED
        if trade.isclosed:
            self.log('OPERATION PROFIT: %s, GROSS %.2f, NET %.2f' %(trade.data._name, trade.pnl, trade.pnlcomm))

            print(self.order_sl[trade.data._name])

            # clear stop loss and take profit order variables for no position state
            if self.order_sl[trade.data._name]:
                print('cancelling SL')
                self.broker.cancel(self.order_sl[trade.data._name])
                self.order_sl[trade.data._name] = None

            if self.order_tp[trade.data._name]:
                print('cancelling TP')
                self.broker.cancel(self.order_tp[trade.data._name])
                self.order_tp[trade.data._name] = None

    def notify_order(self, order):
        '''Receives an order whenever there has been a change in one
            Methods (def in Class) have access to all the data contained on the instance of the object; they can access and modify anything previously set on self.
            Note: "print(order.executed.__dict__)" gives all components of "Order.Executed": {'comm': 9.8, 'psize': 0, 'remsize': 0, 'dt': 735810.0, 'p2': 1, 'pnl': 0.0, 'pclose': 0.0, 'pricelimit': 0.0, 'value': 8134.0, 'margin': None, 'size': -33200, 'p1': 0, 'pprice': 0.0, 'price': 0.245, 'exbits': deque([<backtrader.order.OrderExecutionBit object at 0x0000020FEA2624E0>])}
        '''

        if order.status in [order.Submitted, order.Accepted]: # SUBMITTED: Marks an order as submitted and stores the broker to which it was submitted. ACCEPTED: Marks an order as accepted
            return # Buy/Sell order submitted/accepted to/by broker - Nothing to do

        elif order.status == order.Margin: #Marks an order as having met a margin call
            #self.bar_executed[order.data._name] = len(self) #length of dataframe when enter market (used to calc days held)
            print('MARGIN CALL!!!')
            self.order[order.data._name] = None # clear order variable
            return

        elif order.status == order.Rejected:
            # **Attention: broker could reject order if not enough cash**
            self.log('ORDER REJECTED: %s, Ref: %s, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %(order.data._name, order.ref, order.executed.price, order.executed.value, order.executed.size, order.executed.comm))

        elif order.status == order.Completed: #Marks an order as completely filled

            if order.isbuy():
                if order.info['name'] == 'Enter':
                    self.log('BUY EXECUTED - Entered Long Pos: %s, Ref: %s, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                              order.ref,
                                                                                                                              order.executed.price,
                                                                                                                              order.executed.value,
                                                                                                                              order.executed.size,
                                                                                                                              order.executed.comm))

                    self.bar_executed[order.data._name] = len(self) #length of dataframe when enter market (used to calc days held)
                    self.order[order.data._name] = None # clear order variable

                elif order.info['name'] == 'Exit':
                    #EXITING MARKET (CLOSING SHORT POSITION) - This code MUST come before "BUY EXECUTED - Entering Long Position" because else TP and SL will be created!
                    self.log('BUY EXECUTED - Closed Short Pos: %s, Ref: %s, Price: %.2f, PNL: %.2f, Purchase Cost: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                      order.ref,
                                                                                                                                      order.executed.price,
                                                                                                                                      order.executed.pnl,
                                                                                                                                      order.executed.value,
                                                                                                                                      order.executed.comm))
                    self.order[order.data._name] = None # clear order variable

                elif order.info['name'] == 'Stop':
                    #EXITING MARKET (CLOSING SHORT POSITION) - This code MUST come before "BUY EXECUTED - Entering Long Position" because else TP and SL will be created!
                    self.log('STOP-LOSS (BUY) EXECUTED - Exited Market Posn: %s, Ref: %s, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                            order.ref,
                                                                                                                                            order.executed.price,
                                                                                                                                            order.executed.value,
                                                                                                                                            order.executed.size,
                                                                                                                                            order.executed.comm))
                    self.order_sl[order.data._name] = None # clear order variable

                elif order.info['name'] == 'Take':
                    #EXITING MARKET (CLOSING SHORT POSITION) - This code MUST come before "BUY EXECUTED - Entering Long Position" because else TP and SL will be created!
                    self.log('TAKE-PROFIT (BUY) EXECUTED - Exited Market Posn: %s, Ref: %s, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                              order.ref,
                                                                                                                                              order.executed.price,
                                                                                                                                              order.executed.value,
                                                                                                                                              order.executed.size,
                                                                                                                                              order.executed.comm))
                    self.order_tp[order.data._name] = None # clear order variable
                else:
                    print('**BUY ERROR** -  Unknown Transaction Type')


            elif order.issell():
                if order.info['name'] == 'Enter':
                    #ENTERING MARKET: SHORT POSITION
                    self.log('SELL EXECUTED - Entered Short Posn: %s, Ref: %s, Price: %.2f, PNL: %.2f, Purchase Cost: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                         order.ref,
                                                                                                                                         order.executed.price,
                                                                                                                                         order.executed.pnl,
                                                                                                                                         order.executed.value,
                                                                                                                                         order.executed.comm))
                    self.bar_executed[order.data._name] = len(self) #length of dataframe when enter market (used to calc days held)
                    self.order[order.data._name] = None # clear order variable

                elif order.info['name'] == 'Exit':
                    #EXITING MARKET (CLOSING LONG POSITION)
                    self.log('SELL EXECUTED - Closed Long Pos: %s, Ref: %s, Price: %.2f, PNL: %.2f, Purchase Cost: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                      order.ref,
                                                                                                                                      order.executed.price,
                                                                                                                                      order.executed.pnl,
                                                                                                                                      order.executed.value,
                                                                                                                                      order.executed.comm))
                    self.order[order.data._name] = None # clear order variable

                elif order.info['name'] == 'Stop':
                    #EXITING MARKET (CLOSING SHORT POSITION) - This code MUST come before "BUY EXECUTED - Entering Long Position" because else TP and SL will be created!
                    self.log('STOP-LOSS (SELL) EXECUTED - Exited Market Posn: %s, Ref: %s, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                             order.ref,
                                                                                                                                             order.executed.price,
                                                                                                                                             order.executed.value,
                                                                                                                                             order.executed.size,
                                                                                                                                             order.executed.comm))
                    self.order_sl[order.data._name] = None # clear order variable

                elif order.info['name'] == 'Take':
                    #EXITING MARKET (CLOSING SHORT POSITION) - This code MUST come before "BUY EXECUTED - Entering Long Position" because else TP and SL will be created!
                    self.log('TAKE-PROFIT (SELL) EXECUTED - Exited Market Posn: %s, Ref: %s, Price: %.2f, Cost: %.2f, Size: %.2f, Comm %.2f' %(order.data._name,
                                                                                                                                               order.ref,
                                                                                                                                               order.executed.price,
                                                                                                                                               order.executed.value,
                                                                                                                                               order.executed.size,
                                                                                                                                               order.executed.comm))
                    self.order_tp[order.data._name] = None # clear order variable

                else:
                    print('**BUY ERROR** -  Unknown Transaction Type')

        elif order.status == order.Cancelled: #Marks an order as cancelled
            #status.canceled occurs when: a "self.broker.cancel()" has occured by user
            if order.info['name'] == 'Take':
                self.log('ORDER CANCELLED - TP: %s, Ref: %s' %(order.data._name, order.ref))
                self.order_tp[order.data._name] = None

            elif order.info['name'] == 'Stop':
                self.log('ORDER CANCELLED - SL: %s, Ref: %s' %(order.data._name, order.ref))
                self.order_sl[order.data._name] = None

            else:
                self.log('ORDER CANCELLED - Unknown reason: %s, Ref: %s' %(order.data._name, order.ref))

    def prenext(self):
        '''
        overrides PRENEXT() so that the "NEXT()" calculations run regardless of when each data date range starts.
        Typically PRENEXT would stop NEXT occuring until the minimum period of an indicator has occured, or all dataframe LINES are running.
        '''
        self.next()

    def next(self):  # Methods (def in Class) have access to all the data contained on the instance of the object; they can access and modify anything previously set on self.
        weekday = self.getdatabyname(args.marketindex).datetime.date(0).isoweekday() #Monday = 1, Sunday = 7
        if weekday in range(1,8): # analyse on all weekdays (MONDAY to SUNDAY)
            num_long = 0
            for i, d in enumerate(d for d in self.datas if len(d) and d._name !=args.marketindex):  # Loop through Universe of Stocks. "If Len(d)" is used to check that all datafeeds have delivered values. as if using minute data, some may have had many minutes, 500, and another may not have 1 record yet (if its still on daily)
                position = self.broker.getposition(d)

                if position.size > 0: # Currently LONG
                    daysheld = len(d) - self.bar_executed[d._name] + 1
                    #Log what currently holding
                    self.log('Stock held: %s, Close: %.2f, score: %.2f, scoreyest: %.2f, posn: %.2f, hold days %i' %(d._name,
                                                                                                                     d.close[0],
                                                                                                                     d.lines.TOTAL_SCORE[0],
                                                                                                                     d.lines.TOTAL_SCORE[-1],
                                                                                                                     self.broker.getposition(d).size,
                                                                                                                     daysheld))

                    if self.order_sl[d._name] is None and self.order_tp[d._name] is None: #create Stop-Loss and Take-Profit WHEN IN THE MARKET
                        stop_loss = d.close[-1]*(1.0 - args.stoploss)
                        take_profit = d.close[-1]*(1.0 + args.takeprofit)
                        self.order_sl[d._name] = self.order_target_percent(target = 0.0,
                                                                           data=d,
                                                                           exectype=bt.Order.Stop,
                                                                           price=stop_loss).addinfo(name="Stop")

                        self.order_tp[d._name] = self.order_target_percent(target = 0.0,
                                                                           data=d,
                                                                           exectype=bt.Order.Limit,
                                                                           price=take_profit).addinfo(name="Take")

                    num_long +=1
                    if d.lines.TOTAL_SCORE[0] < args.buyscore:  # NB: Lines[0] = TODAY, lines[-1] = YESTERDAY, lines[-2] = day before yesterday...
                        self.log('CLOSE LONG POSN: %s, Close: %.2f, score: %.2f' %(d._name,
                                                                                   d.close[0],
                                                                                   d.lines.TOTAL_SCORE[0]))
                        self.order[d._name] = self.close(data=d).addinfo(name="Exit")

                elif position.size == 0 and d.lines.TOTAL_SCORE[0] >= args.buyscore: # Currently NOT IN MARKET
                    if self.order[d._name]: #order pending
                        return
                    # BUY!
                    self.log('CREATE BUY: %s, Close: %.2f, score: %.2f' %(d._name,d.close[0],d.lines.TOTAL_SCORE[0]))
                    self.order[d._name] = self.buy(data=d,
                                                   exectype=bt.Order.Limit,
                                                   price=d.close[0]*(1+args.limitpct),
                                                   valid=datetime.datetime.now() + datetime.timedelta(days=args.validdays)).addinfo(name="Enter")

            self.log('Stocks held: %s' %(str(num_long)))

        def stop(self):
            #Print TOTAL PORTFOLIO VALUE
            self.log('Ending Value %.2f' %(self.broker.getvalue()),doprint=True)



class PortfolioSizer(bt.Sizer):
    params = (('stake', 1),)
    def _getsizing(self, comminfo, cash, data, isbuy):
        args = parse_args()
        position = self.broker.getposition(data)
        '''NB: position output options:
        - Size
        - Price
        - Price orig
        - Closed
        - Opened
        - Adjbase'''
        price = data.close[0]
        investment = args.cash * args.pctperstock
        if cash < investment:
            investment = max(cash,args.mintrade) # i.e. we will NEVER invest less than the "mintrade" $value in a particular stock
        qty = math.floor(investment/price) #buys quantities in accordance with allocated % per stock, or the remaining cash left over..provided it is greater than the "mintrade" value

        if isbuy:  # if buying
            if position.size < 0:  # if currently short, buy the amount which are short to close out trade.
                return -position.size  # This method returns the desired size for the buy/sell operation
            if position.size > 0:
                return 0  # dont buy if already hold
            return qty  # num. stocks to buy

        if not isbuy:  # if selling..
            if position.size < 0:
                return 0  # dont sell if already SHORT
            if position.size > 0:
                return position.size  # was previously a buy... sell what currently hold
            return qty  # num. stocks to SHORT


class CustomDataLoader(btfeeds.PandasData):
    lines = ('TOTAL_SCORE', 'Beta',)
    params = (
        ('openinterest', None),     # None= column not present
        ('TOTAL_SCORE', -1),        # -1 = autodetect position or case-wise equal name
        ('Beta', -1))
    datafields = btfeeds.PandasData.datafields + (['TOTAL_SCORE', 'Beta'])
