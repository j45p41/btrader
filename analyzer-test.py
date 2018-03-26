from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime

import backtrader as bt
import backtrader.observers as btobservers
import backtrader.analyzers as btanalyzers
import backtrader.feeds as btfeeds
import backtrader.strategies as btstrats

cerebro = bt.Cerebro()

# data
dataname = 'C:/Users/Jaspal/OneDrive/Financial Stuff/btrader_git/datas/2005-2006-day-001.txt'
data = btfeeds.BacktraderCSVData(dataname=dataname)

cerebro.adddata(data)

# strategy
cerebro.addstrategy(btstrats.SMA_CrossOver)

# Analyzer
cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')
cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='mytrades')
cerebro.addanalyzer(btanalyzers.Transactions, _name='mytransactions')
cerebro.addanalyzer(btanalyzers.PeriodStats, _name='mytperiodstats')

#Obervers
#cerebro.addobserver(btobservers.Trades, _name='myobservers')



thestrats = cerebro.run()
thestrat = thestrats[0]

#print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis())
print('TradeAnalyser:', thestrat.analyzers.mytrades.get_analysis())
#print('Transactions:', thestrat.analyzers.mytransactions.get_analysis())
#print('Transactions:', thestrat.analyzers.mytperiodstats.get_analysis())

cerebro.plot(style='candlestick')

