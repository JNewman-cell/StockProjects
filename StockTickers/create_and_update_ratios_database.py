import sqlite3
from csv_manipulation import extract_all_valid_tickers_from_csvs
from tqdm import tqdm
from yahooquery import Ticker
import time

def check_ratios(ticker, info, field):
    try:
        return info.get(field, None)
    except Exception as e:
        print(f"Error getting {field} for {ticker}: {e}")
        return None

def extract_stock_info(ticker):
    """
    Extract the financial ratios data of a ticker.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    dict: The financial ratios of the ticker
    """
    data = {}
    try:
        # Initialize Ticker object with extended timeout
        stock = Ticker(ticker, timeout=30)
        
        # Get quotes and summary data
        quotes = stock.quotes[ticker] if isinstance(stock.quotes, dict) else {}
        summary = stock.summary_detail[ticker] if isinstance(stock.summary_detail, dict) else {}
        key_stats = stock.key_stats[ticker] if isinstance(stock.key_stats, dict) else {}
        financial_data = stock.financial_data[ticker] if isinstance(stock.financial_data, dict) else {}
        
        # Combine all data sources
        ratios = {**quotes, **summary, **key_stats, **financial_data}
        
        # Extract data including the company name
        data = {
            'name': ratios.get('longName', 'N/A'),
            'profitMargins': check_ratios(ticker, ratios, 'profitMargins'),
            'payoutRatio': check_ratios(ticker, ratios, 'payoutRatio'),
            'dividendYield': check_ratios(ticker, ratios, 'dividendYield'),
            'twoHundredDayAverage': check_ratios(ticker, ratios, 'twoHundredDayAverage'),
            'fiftyDayAverage': check_ratios(ticker, ratios, 'fiftyDayAverage'),
            'totalCash': check_ratios(ticker, ratios, 'totalCash'),
            'totalDebt': check_ratios(ticker, ratios, 'totalDebt'),
            'earningsGrowth': check_ratios(ticker, ratios, 'earningsGrowth'),
            'revenueGrowth': check_ratios(ticker, ratios, 'revenueGrowth'),
            'trailingPE': check_ratios(ticker, ratios, 'trailingPE'),
            'forwardPE': check_ratios(ticker, ratios, 'forwardPE'),
            'trailingEps': check_ratios(ticker, ratios, 'trailingEps'),
            'forwardEps': check_ratios(ticker, ratios, 'forwardEps'),
            'ebitda': check_ratios(ticker, ratios, 'ebitda'),
            'freeCashflow': check_ratios(ticker, ratios, 'freeCashflow'),
            'marketCap': check_ratios(ticker, ratios, 'marketCap')
        }
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        # Fill with N/A values for all fields
        data = {field: None for field in [
            'name', 'profitMargins', 'payoutRatio', 'dividendYield', 'twoHundredDayAverage',
            'fiftyDayAverage', 'totalCash', 'totalDebt', 'earningsGrowth', 'revenueGrowth',
            'trailingPE', 'forwardPE', 'trailingEps', 'forwardEps', 'ebitda', 'freeCashflow',
            'marketCap'
        ]}
        
    return data

def create_database():
    """
    Creates the database for the financial ratios of each company.

    Parameters:
	None

    Returns:
    sqlite3.conn: Connection to the financial ratio database.
    """
    conn = sqlite3.connect('FlaskApp/stock_info.db')
    cursor = conn.cursor()

    # Create tables with the new structure including the company name, freeCashflow, and marketCap
    cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        ticker TEXT NOT NULL,
                        profitMargins REAL,
                        payoutRatio REAL,
                        dividendYield REAL,
                        twoHundredDayAverage REAL,
                        fiftyDayAverage REAL,
                        totalCash REAL,
                        totalDebt REAL,
                        earningsGrowth REAL,
                        revenueGrowth REAL,
                        trailingPE REAL,
                        forwardPE REAL,
                        trailingEps REAL,
                        forwardEps REAL,
                        ebitda REAL,
                        freeCashflow REAL,
                        marketCap REAL,
                        UNIQUE (ticker)
                    )''')

    conn.commit()
    return conn

def insert_data_into_database(conn, ticker, data):
    """
    Insert the yearly financial data into the database.

    Parameters:
	conn (sqlite3.conn): The connection to the dividend database.
    ticker (str): The ticker symbol of the company.
	data (dict): The financial ratio data for the ticker.

    Returns:
    None
    """
    cursor = conn.cursor()

    # Prepare the data for insertion or update including the company name, freeCashflow, and marketCap
    values = (data['name'], ticker, data['profitMargins'], data['payoutRatio'], data['dividendYield'],
              data['twoHundredDayAverage'], data['fiftyDayAverage'], data['totalCash'],
              data['totalDebt'], data['earningsGrowth'], data['revenueGrowth'],
              data['trailingPE'], data['forwardPE'], data['trailingEps'], data['forwardEps'],
              data['ebitda'], data['freeCashflow'], data['marketCap'])

    # Insert or update the data including the company name, freeCashflow, and marketCap
    cursor.execute('''INSERT INTO stocks (name, ticker, profitMargins, payoutRatio, dividendYield,
                                          twoHundredDayAverage, fiftyDayAverage, totalCash, totalDebt,
                                          earningsGrowth, revenueGrowth, trailingPE, forwardPE,
                                          trailingEps, forwardEps, ebitda, freeCashflow, marketCap)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      ON CONFLICT(ticker) DO UPDATE SET
                      name=excluded.name,
                      profitMargins=excluded.profitMargins,
                      payoutRatio=excluded.payoutRatio,
                      dividendYield=excluded.dividendYield,
                      twoHundredDayAverage=excluded.twoHundredDayAverage,
                      fiftyDayAverage=excluded.fiftyDayAverage,
                      totalCash=excluded.totalCash,
                      totalDebt=excluded.totalDebt,
                      earningsGrowth=excluded.earningsGrowth,
                      revenueGrowth=excluded.revenueGrowth,
                      trailingPE=excluded.trailingPE,
                      forwardPE=excluded.forwardPE,
                      trailingEps=excluded.trailingEps,
                      forwardEps=excluded.forwardEps,
                      ebitda=excluded.ebitda,
                      freeCashflow=excluded.freeCashflow,
                      marketCap=excluded.marketCap''', values)

    conn.commit()

def printDB():
    """
    Prints out the entire database for the financial ratios of each company.

    Parameters:
	None

    Returns:
    None
    """
    try:
        conn = sqlite3.connect('FlaskApp/stock_info.db')
        c = conn.cursor()
        c.execute('SELECT * FROM stocks')
        rows = c.fetchall()

        if not rows:
            print("No data found in the 'stocks' table.")
        else:
            for row in rows:
                print(row)

    except sqlite3.Error as e:
        print(f"Error reading data from database: {e}")
    finally:
        if conn:
            conn.close()

def main():
    conn = create_database()

    tickers = extract_all_valid_tickers_from_csvs()

    for ticker in tqdm(tickers, desc="Updating financial ratio database"):
        data = extract_stock_info(ticker)
        insert_data_into_database(conn, ticker, data)
        time.sleep(1)
    conn.close()

    # Uncomment the following line if you want to print the database contents
    # printDB()

if __name__ == "__main__":
    main()
