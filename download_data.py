import yfinance as yf
import datetime

msft = yf.Ticker("MSFT")

# # get all stock info
print(msft.info)

# # get historical market data
# hist = msft.history(period="5yr")

# end_date = datetime.datetime.now()
# start_date = end_date - datetime.timedelta(days=5*365)

# stock_data = yf.download("MSFT", start=start_date, end=end_date, interval='1wk')

# print(stock_data)