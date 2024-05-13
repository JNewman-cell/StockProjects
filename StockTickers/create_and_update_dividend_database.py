import sqlite3
import yfinance as yf
import pandas as pd
from collections import defaultdict
import csv
import time
import datetime

tickers = []

def extract_tickers_from_csv(file_path):
	with open(file_path, newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			frequency = row['Market Cap']
			if frequency != 'N/A':
				tickers.append(row['Ticker'])
	return tickers

def extract_dividend_data(ticker):
    # Fetch dividend data using yfinance
    ticker_obj = yf.Ticker(ticker)

    # Define date range for the last 10 years
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365 * 15)
    start_date = start_date.replace(tzinfo=datetime.timezone.utc)  # Make start_date timezone-aware

    # Fetch and filter dividend data
    div_data = ticker_obj.history(start=start_date, end=end_date).Dividends
    history = ticker_obj.history(start=start_date, end=end_date)
    if 'Dividends' in history.columns:
        div_data = history.Dividends
        dividends = [{'date': date.strftime('%Y-%m'), 'amount': float(amount)} for date, amount in div_data.items() if amount > 0]
    else:
        dividends = []

    return dividends

def create_database():
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
	cursor = conn.cursor()

	for dateamount in data:
		cursor.execute('''INSERT OR IGNORE INTO stocks (ticker, date, dividend)
							VALUES (?, ?, ?)''',
						(ticker, dateamount['date'], dateamount['amount']))

	conn.commit()

def printDB():
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
    # conn = create_database()

    # Get the tickers from the data
    csv_file_path = 'StockTickers/nasdaq_tickers_cleaned.csv'
    csv_file_path2 = 'StockTickers/nyse_tickers_cleaned.csv'
    extract_tickers_from_csv(csv_file_path)
    extract_tickers_from_csv(csv_file_path2)

    # test ticker set
    # tickers = ['AAPL', 'GOOGL']
    # print(len(tickers))

    for ticker in tickers:
        data = extract_dividend_data(ticker)
        insert_data_into_database(conn, ticker, data)
    conn.close()

    printDB()

if __name__ == "__main__":
    main()
