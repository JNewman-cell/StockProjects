import sqlite3
import datetime
import time
from collections import defaultdict
from csv_manipulation import extract_all_valid_tickers_from_csvs
from CRUD_ex_dividend_database import get_tickers_with_dividend_within_a_week
from tqdm import tqdm
from yahooquery import Ticker
import pandas as pd

def extract_dividend_data(ticker):
    """
    Extract the dividend data of a ticker for the last 15 years.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    list: Holding each years the last 15 years of a tickers dividend data
    """
    try:
        # Initialize Ticker object with extended timeout
        ticker_obj = Ticker(ticker, timeout=30)
        
        # Define date range for the last 15 years
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=365 * 15)
        
        # Fetch dividend data using yahooquery
        div_history = ticker_obj.dividend_history(start=start_date, end=end_date)
        
        if isinstance(div_history, pd.DataFrame) and not div_history.empty:
            dividends = []
            for _, row in div_history.iterrows():
                if row['dividend'] > 0:
                    dividends.append({
                        'date': row['date'].strftime('%Y-%m'),
                        'amount': float(row['dividend'])
                    })
            return dividends
        return []
        
    except Exception as e:
        print(f"Error fetching dividend data for {ticker}: {e}")
        return []

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
    
    tickers = get_tickers_with_dividend_within_a_week()

    # test ticker set
    # tickers = ['AAPL', 'GOOGL']
    # print(len(tickers))

    for ticker in tqdm(tickers, desc="Updating dividends database"):
        data = extract_dividend_data(ticker)
        insert_data_into_database(conn, ticker, data)
        time.sleep(1)
    conn.close()

	# Uncomment the following line if you want to print the database contents
    # printDB()

if __name__ == "__main__":
    main()
