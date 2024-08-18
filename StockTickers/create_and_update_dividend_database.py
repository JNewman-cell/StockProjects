import sqlite3
import yfinance as yf
import pandas as pd
from collections import defaultdict
from csv_manipulation import extract_all_valid_tickers_from_csvs
import time
import datetime

def extract_dividend_data(ticker):
    """
    Extract the dividend data of a ticker for the last 15 years.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    list: Holding each years the last 15 years of a tickers dividend data
    """
    # Fetch dividend data using yfinance
    ticker_obj = yf.Ticker(ticker)
    print(ticker)

    # Define date range for the last 10 years
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365 * 15)
    start_date = start_date.replace(tzinfo=datetime.timezone.utc)  # Make start_date timezone-aware

    # Fetch and filter dividend data
    history = ticker_obj.history(start=start_date, end=end_date)
    if 'Dividends' in history.columns:
        div_data = history.Dividends
        dividends = [{'date': date.strftime('%Y-%m'), 'amount': float(amount)} for date, amount in div_data.items() if amount > 0]
    else:
        dividends = []

    return dividends

def create_database():
    """
    Creates the database for the dividend history of each company.

    Parameters:
	None

    Returns:
    sqlite3.conn: connection to the dividend database.
    """
    conn = sqlite3.connect('FlaskApp/dividend_data.db')
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY,
                        ticker TEXT NOT NULL,
                        date TEXT NOT NULL,
                        dividend REAL,
                        UNIQUE (ticker, date)
                    )''')

    conn.commit()
    return conn

def insert_data_into_database(conn, ticker, data):
    """
    Insert the yearly financial data into the database.

    Parameters:
	conn (sqlite3.conn): The connection to the dividend database.
    ticker (str): The ticker symbol of the company.
	data (dict): The dividend data for the last 15 years.

    Returns:
    None
    """
    cursor = conn.cursor()

    # Prepare a list of tuples to be inserted
    rows_to_insert = [(ticker, dateamount['date'], dateamount['amount']) for dateamount in data]

    # Use executemany to insert all rows in a single operation
    cursor.executemany('''INSERT OR IGNORE INTO stocks (ticker, date, dividend)
                          VALUES (?, ?, ?)''', rows_to_insert)

    conn.commit()

def get_latest_dividend_of_ticker(ticker):
	"""
	Insert the yearly financial data into the database.

	Parameters:
	conn (sqlite3.conn): The connection to the dividend database.
	ticker (str): The ticker symbol of the company.
	data (dict): The dividend data for the last 15 years.

	Returns:
	None
	"""
	conn = sqlite3.connect('FlaskApp/dividend_data.db')
	cursor = conn.cursor()


	cursor.execute("SELECT * FROM stocks WHERE ticker = ? ORDER BY id DESC Limit 1",(ticker,))
	# cursor.execute("SELECT * FROM stocks ORDER BY date(date) DESC Limit 1 WHERE ticker = ?", (ticker,))
	result = cursor.fetchall()
	# print(result)

	conn.close()

	return result[0][2] if result else None

def printDB():
    """
    Prints out the entire database for the dividends of each company.

    Parameters:
	None

    Returns:
    None
    """
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('FlaskApp/dividend_data.db')
        c = conn.cursor()

        # Execute a SELECT query to fetch all rows from the table
        c.execute('SELECT * FROM stocks')

        # Fetch all rows from the result cursor
        rows = c.fetchall()

        if not rows:
            print("No data found in the 'stocks' table.")
        else:
            # Print the fetched rows
            for row in rows:
                print(row)

    except sqlite3.Error as e:
        print(f"Error reading data from database: {e}")

    finally:
        # Close the connection
        if conn:
            conn.close()

def main():
    # Create database and get connection
    conn = sqlite3.connect('FlaskApp/dividend_data.db')
    
    tickers = extract_all_valid_tickers_from_csvs()

    # test ticker set
    # tickers = ['AAPL', 'GOOGL']
    # print(len(tickers))

    for ticker in tickers:
        data = extract_dividend_data(ticker)
        insert_data_into_database(conn, ticker, data)
        time.sleep(1)
    conn.close()

	# Uncomment the following line if you want to print the database contents
    # printDB()

if __name__ == "__main__":
    main()
