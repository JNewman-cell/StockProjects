import yfinance as yf
import datetime
import time
import pytz
import sqlite3

def time_api_call(route_function):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = route_function(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time
    return wrapper

# Function to connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('FlaskApp/financial_data.db')
    return conn

# Function to connect to the dividend SQLite database
def connect_dividend_db():
    conn = sqlite3.connect('FlaskApp/dividend_data.db')
    return conn

@time_api_call
def companyinfo_api(ticker):
    stock = yf.Ticker(ticker)
    print(stock.info)

@time_api_call
def companyinfo_database(ticker):
    conn = sqlite3.connect('FlaskApp/stock_info.db')
    cursor = conn.cursor()
    cursor.execute("SELECT profitMargins, payoutRatio, dividendYield, twoHundredDayAverage, fiftyDayAverage, totalCash, totalDebt, earningsGrowth, revenueGrowth, trailingPE, forwardPE, trailingEps, forwardEps, ebitda, freeCashflow, marketCap, name FROM stocks WHERE ticker = ?", (ticker,))
    data = cursor.fetchall()
    columns = ['Profit Margin', 'Payout Ratio', 'Dividend Yield',
               '200 Day MA', '50 Day MA', 'Total Cash', 'Total Debt',
               'Earnings Growth', 'Revenue Growth', 'Trailing PE', 'Forward PE',
               'Trailing EPS', 'Forward EPS', 'EBITDA', 'Free Cash Flow', 'Market Cap', 'Name']
    formatted_data = []

    formatted_data.append(dict(zip(columns, data)))

    conn.close()

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
def dividend_api(ticker):
    # Fetch dividend data using yfinance
    ticker_obj = yf.Ticker(ticker)
    
    # Define date range for the last 10 years
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365 * 15)
    start_date = start_date.replace(tzinfo=datetime.timezone.utc)  # Make start_date timezone-aware

    # Fetch and filter dividend data
    div_data = ticker_obj.history(start=start_date, end=end_date).Dividends
    dividends = [{'date': date.strftime('%Y-%m'), 'amount': float(amount)} for date, amount in div_data.items() if amount > 0]

    return dividends

@time_api_call
def dividend_database(ticker):
    conn = connect_dividend_db()
    cursor = conn.cursor()
    cursor.execute("SELECT date, dividend FROM stocks WHERE ticker = ? ORDER BY date", (ticker,))
    data = cursor.fetchall()
    conn.close()

@time_api_call
def financials_api(ticker):
    stock = yf.Ticker(ticker)
    income_stmt = stock.income_stmt
    cashflow = stock.cashflow
    balance_sheet = stock.balance_sheet

@time_api_call
def financials_database(ticker):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT year, revenue, ebitda, fcf, sbc, net_income, eps, cash, debt, shares_outstanding FROM stocks WHERE ticker = ? ORDER BY year", (ticker,))
    data = cursor.fetchall()
    conn.close()

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
    ticker = 'AMZN'

    api_times = {}
    db_times = {}
    differences = {}

    # Measure times
    api_times['companyinfo'] = companyinfo_api(ticker)
    db_times['companyinfo'] = companyinfo_database(ticker)
    db_times['dividends'] = dividend_database(ticker)
    api_times['dividends'] = dividend_api(ticker)
    db_times['financials'] = financials_database(ticker)
    api_times['financials'] = financials_api(ticker)

    # Calculate differences
    for key in api_times:
        differences[key] = api_times[key] - db_times[key]

    total_difference = sum(differences.values())
    total_api_time = sum(api_times.values())
    total_db_time = sum(db_times.values())
    percent_difference = (total_difference / total_api_time) * 100 if total_api_time != 0 else 0

    # Output the results
    for key in differences:
        print(f"{key} difference: {differences[key]:.4f} seconds")

    print(f"Total difference: {total_difference:.4f} seconds")
    print(f"Total percent difference: {percent_difference:.2f}%")
