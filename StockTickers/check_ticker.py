import yfinance as yf
import time
import datetime
from dateutil.relativedelta import relativedelta
from CRUD_ex_dividend_database import get_ex_dividend_date_API, get_latest_dividend_of_ticker

from csv_manipulation import extract_all_valid_tickers_from_csvs

from clean_datasets import get_market_cap

print(get_market_cap('AAPL'))

today = datetime.datetime.today()
one_week_from_now = today + datetime.timedelta(days=7)
seven_months_back = today + relativedelta(months=-7)

ticker_obj = yf.Ticker('AMZN')
earnings_info = ticker_obj.calendar
# print(earnings_info)

# Define date range for the last 10 years
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365 * 15)
start_date = start_date.replace(tzinfo=datetime.timezone.utc)  # Make start_date timezone-aware

# Fetch and filter dividend data
history = ticker_obj.history(start=start_date, end=end_date)
print(get_latest_dividend_of_ticker('AAPL'))
print(get_ex_dividend_date_API('AAPL'))

nodividends=0
nodividendswithinsevenmonths=0
nodividendswithexdividend=0
dividends=0
print(seven_months_back.year)
print(seven_months_back.month)

# for ticker in extract_all_valid_tickers_from_csvs():
# 	date = get_latest_dividend_of_ticker(ticker)
# 	# print(date)
# 	# print(date[:4])
# 	# print(date[-2:])
# 	if date==None:
# 		if get_ex_dividend_date_API(ticker):
# 			nodividendswithexdividend+=1
# 			time.sleep(0.2)
# 		nodividends+=1
# 	else:
# 		dividends+=1
# 		# print(ticker)

print('Tickers with Dividends:'+str(dividends))
print('Tickers with No Dividends:'+str(nodividends))
print('Tickers with No Dividends With Ex Dividend:'+str(nodividendswithexdividend))