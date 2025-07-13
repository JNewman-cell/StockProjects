import yfinance as yf

ticker_obj = yf.Ticker('AMZN')
print(ticker_obj.info)