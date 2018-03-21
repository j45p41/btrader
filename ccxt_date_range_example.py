import ccxt
poloniex = ccxt.poloniex()
start = poloniex.parse8601('2017-01-15 00:00:00')
end = poloniex.parse8601('2017-01-17 00:00:00')  # inclusive
end_v = { 'end': int(end/1000)}
ohlcv = poloniex.fetch_ohlcv("ETH/BTC", '5m', start, None, { 'end': int(end/1000)})
for entry in ohlcv:
    print('Example B', poloniex.iso8601(entry[0]), entry[1:5])