
import ccxt
from datetime import datetime, timedelta, timezone
import math
import pandas as pd


symbol = str('BTC/USDT')
timeframe = str('15m')
exchange = str('poloniex')
exchange_out = str(exchange)
# Get our Exchange
exchange = getattr (ccxt, exchange) ()


# Get data
data = exchange.fetch_ohlcv(symbol, timeframe,since=1424378700000, limit=10)
header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
df = pd.DataFrame(data, columns=header).set_index('Timestamp')
# Save it
symbol_out = symbol.replace("/","")
filename = '{}-{}-{}.csv'.format(exchange_out, symbol_out,timeframe)
df.to_csv(filename)