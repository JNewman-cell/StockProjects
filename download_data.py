import yfinance as yf
import datetime
import time
import pytz

def time_api_call(route_function):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = route_function(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time
    return wrapper

@time_api_call
def prices(ticker):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=5*365)

    # Download stock price data
    stock_data = yf.download(ticker, start=start_date, end=end_date, interval='1wk')
    
    # Extract date and closing price
    dates = stock_data.index.strftime('%Y-%m-%d').tolist()
    prices = stock_data['Close'].tolist()
    
    return {'dates': dates, 'prices': prices}

@time_api_call
def dividends(ticker):
    # Fetch dividend data using yfinance
    ticker_obj = yf.Ticker(ticker)
    
    # Define date range for the last 10 years
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365 * 10)
    start_date = start_date.replace(tzinfo=datetime.timezone.utc)  # Make start_date timezone-aware

    # Fetch and filter dividend data
    div_data = ticker_obj.history(start=start_date, end=end_date).Dividends
    dividends = [{'date': date.strftime('%Y-%m'), 'amount': float(amount)} for date, amount in div_data.items() if amount > 0]

    return dividends
  
def dividendsCheck(ticker):
    ticker = ticker
    # Fetch dividend data using yfinance
    div_data = yf.Ticker(ticker).dividends
    # Filter dividend data for the last 10 years
    end_date = datetime.datetime.now(pytz.utc)
    start_date = end_date - datetime.timedelta(days=365 * 10)
    start_date = start_date.replace(tzinfo=pytz.utc)  # Make start_date timezone-aware
    # Filter dividends and remove timestamps
    dividends = [{'date': date.strftime('%Y-%m'), 'amount': float(amount)} for date, amount in div_data.items() if date >= start_date]
    return dividends

if __name__ == '__main__':
	ticker = 'MSFT'

	start_time = time.time()
	stock = yf.Ticker(ticker)
	print(stock.info)
    # income_stmt = stock.income_stmt
    # cashflow = stock.cashflow
    # balance_sheet = stock.balance_sheet
    # end_time = time.time()
    # print(end_time-start_time)
    # start_time = time.time()
    # end_date = datetime.datetime.now()
    # start_date = end_date - datetime.timedelta(days=365 * 15)
    # start_date = start_date.replace(tzinfo=datetime.timezone.utc)  # Make start_date timezone-aware

    # # Fetch and filter dividend data
    # div_data = stock.history(start=start_date, end=end_date).Dividends
    # end_time = time.time()
    # print(end_time-start_time)

    # performance testing for APIs
    # # List of 100 stock tickers
    # tickers = [
    #     "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-A", "JNJ", "V", "WMT",
    #     "PG", "JPM", "MA", "NVDA", "DIS", "HD", "BAC", "UNH", "INTC", "VZ",
    #     "PYPL", "CMCSA", "ADBE", "NFLX", "PFE", "KO", "MRK", "T", "CRM", "PEP",
    #     "ABBV", "NKE", "XOM", "CSCO", "CVX", "BA", "WFC", "TMO", "ABT", "PM",
    #     "ORCL", "AMGN", "AMD", "ACN", "IBM", "QCOM", "MDT", "DHR", "HON", "NEE",
    #     "LOW", "COST", "SBUX", "INTU", "UNP", "MMM", "LMT", "TXN", "RTX", "LIN",
    #     "UPS", "NOW", "GS", "MS", "BDX", "ISRG", "FIS", "GILD", "SYK",
    #     "CVS", "DE", "SPGI", "VRTX", "VRTX", "ZTS", "TMUS", "AMAT", "CL", "MO",
    #     "BKNG", "CAT", "FDX", "FISV", "BIIB", "CI", "MMC", "ADI", "ADP", "ITW",
    #     "PNC", "TFC", "DUK", "PLD", "ECL", "BSX", "EW", "SO", "GM"
    # ]

    # # Measure average time for prices
    # prices_total_time = sum(prices(ticker) for ticker in tickers)
    # prices_avg_time = prices_total_time / (len(tickers))

    # # Measure average time for dividends
    # dividends_total_time = sum(dividends(ticker) for ticker in tickers)
    # dividends_avg_time = dividends_total_time / (len(tickers))

    # print(f"Average time taken for prices (over {len(tickers)} stocks): {prices_avg_time*1000} milliseconds")
    # print(f"Average time taken for dividends (over {len(tickers)} stocks): {dividends_avg_time*1000} milliseconds")
