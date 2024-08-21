import yfinance as yf
import sqlite3
import json
import datetime
import time
from csv_manipulation import extract_all_valid_tickers_from_csvs
from tqdm import tqdm

def get_earnings_date_API(ticker):
    """
    Get the earnings date of a company using its ticker symbol from yfinance.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    str: The earnings date of the company.
    """
    ticker_obj = yf.Ticker(ticker)
    earnings_info = ticker_obj.calendar
    # print(earnings_info)

    if 'Earnings Date' in earnings_info:
        try:
            earnings_date = earnings_info['Earnings Date'][0]
        except Exception as e:
            earnings_date = None
        return earnings_date
    else:
        return None

def get_earnings_date_DB(ticker):
    """
    Get the entire row of a company using its ticker symbol from DB.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    tuple: The entire row of the company.
    """
    conn = sqlite3.connect('FlaskApp/earnings_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT date FROM stocks WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()

    conn.close()

    return result

def ticker_in_database(ticker):
    """
    Check if a ticker is present in the database.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    bool: True if the ticker is present, False otherwise.
    """
    conn = sqlite3.connect('FlaskApp/earnings_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM stocks WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()

    conn.close()

    return result is not None

def get_tickers_with_earnings_within_a_week():
    tickers_with_earnings = []
    
    with open('StockTickers/weekly_earnings.json', 'r') as jsonfile:
        tickers_with_earnings = json.load(jsonfile)

    return tickers_with_earnings

def create_database():
    """
    Creates the database for the yearly financials of each company.

    Parameters:
    None

    Returns:
    conn (sqlite3.Connection): connection to the yearly financial database.
    """
    conn = sqlite3.connect('FlaskApp/earnings_data.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY,
                        ticker TEXT NOT NULL,
                        date TEXT NOT NULL
                    )''')

    conn.commit()
    return conn

def insert_data_into_database(conn, ticker, earnings_date):
    """
    Insert the earnings date into the database if it is within a week of today.

    Parameters:
    conn (sqlite3.Connection): The database connection.
    ticker (str): The ticker symbol of the company.
    earnings_date (str): The earnings date of the company.

    Returns:
    None
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stocks (ticker, date) VALUES (?, ?)", (ticker, earnings_date))
    conn.commit()

def delete_ticker_from_database(conn, ticker):
    """
    Delete an entry from the database using its ticker symbol.

    Parameters:
    conn (sqlite3.Connection): The database connection.
    ticker (str): The ticker symbol of the company.

    Returns:
    None
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks WHERE ticker = ?", (ticker,))
    conn.commit()

def printDB():
    try:
        conn = sqlite3.connect('FlaskApp/earnings_data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM stocks')
        rows = c.fetchall()

        if not rows:
            print("No data found in the 'stocks' table.")
        else:
            # print the fetched rows
            for row in rows:
                print(row)

    except sqlite3.Error as e:
        print(f"Error reading data from database: {e}")

    finally:
        # Close the connection
        if conn:
            conn.close()

def update_earnings_db_and_weekly_earnings():
    conn = create_database()
    tickers = extract_all_valid_tickers_from_csvs()

    # tickers = ['AAPL', 'MSFT', 'NFLX']
    new_weekly_earnings = []
    with open('StockTickers/weekly_earnings.json', 'r') as jsonfile:
        weekly_earnings = json.load(jsonfile)

    today = datetime.datetime.today()
    one_week_from_now = today + datetime.timedelta(days=7)
    # printDB()
        
    for ticker in tqdm(tickers, desc="Updating earnings and weekly earnings"):
        # ticker is not in the database, indicating that it should be checked
        if not ticker_in_database(ticker):
            # ticker is not in the weekly_earnings database meaning we have to fetch the data from the API
            earnings_date = get_earnings_date_API(ticker)
            # print(ticker)
            # print(earnings_date)
            # earnings date is in the yfinance API
            if earnings_date != None:
                try:
                    # print(earnings_date)
                    # convert datetime.date to datetime.dateime to compare to today's date
                    earnings_comp = datetime.datetime(earnings_date.year, earnings_date.month, earnings_date.day)
                except Exception as e:
                    continue
                # earnings are not coming up in the next week, no need to check the earnings
                if not today <= earnings_comp <= one_week_from_now:
                    insert_data_into_database(conn, ticker, earnings_date)
                else:
                    # earnings are coming up and it wasn't found in the weekly earnings list, therefore we should check for report
                    if ticker not in weekly_earnings:
                        new_weekly_earnings.append(ticker)
            time.sleep(1)
        elif ticker_in_database(ticker):
            # if the ticker is in the database, do the same comparison to find the new upcoming weekly earnings
            earnings_date = datetime.datetime.strptime(get_earnings_date_DB(ticker)[0], "%Y-%m-%d").date()
            # print(earnings_date)
            earnings_comp = datetime.datetime(earnings_date.year, earnings_date.month, earnings_date.day)
            if not today <= earnings_comp <= one_week_from_now:
                delete_ticker_from_database(conn, ticker)
                new_weekly_earnings.append(ticker)

    # save the list of tickers with upcoming earnings to a json file for use in other scripts
    with open('StockTickers/weekly_earnings.json', 'w') as jsonfile:
        json.dump(new_weekly_earnings, jsonfile)

    conn.close()

def main():
	printDB()

if __name__ == "__main__":
    main()
