import yfinance as yf
import sqlite3
import json
import datetime
from dateutil.relativedelta import relativedelta
import time
from csv_manipulation import extract_all_valid_tickers_from_csvs
from tqdm import tqdm

def get_ex_dividend_date_API(ticker):
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

    if 'Ex-Dividend Date' in earnings_info:
        try:
            ex_dividend_date = earnings_info['Ex-Dividend Date']
        except Exception as e:
            ex_dividend_date = None
        return ex_dividend_date
    else:
        return None

def get_ex_dividend_date_DB(ticker):
    """
    Get the entire row of a company using its ticker symbol from DB.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    tuple: The entire row of the company.
    """
    conn = sqlite3.connect('FlaskApp/ex_dividend_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT date FROM stocks WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()

    conn.close()

    return result

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

def ticker_in_database(ticker):
    """
    Check if a ticker is present in the database.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    bool: True if the ticker is present, False otherwise.
    """
    conn = sqlite3.connect('FlaskApp/ex_dividend_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM stocks WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()

    conn.close()

    return result is not None

def get_tickers_with_dividend_within_a_week():
    tickers_with_dividend = []
    
    with open('StockTickers/weekly_dividends.json', 'r') as jsonfile:
        tickers_with_dividends = json.load(jsonfile)

    return tickers_with_dividends

def create_database():
    """
    Creates the database for the yearly financials of each company.

    Parameters:
    None

    Returns:
    conn (sqlite3.Connection): connection to the yearly financial database.
    """
    conn = sqlite3.connect('FlaskApp/ex_dividend_data.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY,
                        ticker TEXT NOT NULL,
                        date TEXT NOT NULL
                    )''')

    conn.commit()
    return conn

def insert_data_into_database(conn, ticker, ex_dividend_date):
    """
    Insert the earnings date into the database if it is within a week of today.

    Parameters:
    conn (sqlite3.Connection): The database connection.
    ticker (str): The ticker symbol of the company.
    ex_dividend_date (str): The earnings date of the company.

    Returns:
    None
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stocks (ticker, date) VALUES (?, ?)", (ticker, ex_dividend_date))
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
        conn = sqlite3.connect('FlaskApp/ex_dividend_data.db')
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

def update_ex_dividends_db_and_weekly_dividends():
    conn = create_database()
    tickers = extract_all_valid_tickers_from_csvs()

    # tickers = ['AAPL', 'MSFT', 'NFLX']
    new_weekly_dividends = []
    with open('StockTickers/weekly_dividends.json', 'r') as jsonfile:
        weekly_dividends = json.load(jsonfile)

    today = datetime.datetime.today()
    one_week_from_now = today + datetime.timedelta(days=7)
    # printDB()
        
    for ticker in tqdm(tickers, desc="Updating ex-dividends and weekly dividends"):
        # print(get_latest_dividend_of_ticker(ticker))
        # tickers' last dividend was greater than seven months ago, so don't check
        date = get_latest_dividend_of_ticker(ticker)
        if date:
            # ticker is not in the database, indicating that it should be checked
            if not ticker_in_database(ticker):
                # ticker is not in the weekly_dividends database meaning we have to fetch the data from the API
                ex_dividend_date = get_ex_dividend_date_API(ticker)
                # print(ticker)
                # print(ex_dividend_date)
                # earnings date is in the yfinance API
                if ex_dividend_date != None:
                    try:
                        # print(ex_dividend_date)
                        # convert datetime.date to datetime.dateime to compare to today's date
                        date_comp = datetime.datetime(ex_dividend_date.year, ex_dividend_date.month, ex_dividend_date.day)
                    except Exception as e:
                        continue
                    # earnings are not coming up in the next week, no need to check the earnings
                    if today <= date_comp and not date_comp <= one_week_from_now:
                        insert_data_into_database(conn, ticker, ex_dividend_date)
                    else:
                        # earnings are coming up and it wasn't found in the weekly earnings list, therefore we should check for report
                        if ticker not in weekly_dividends:
                            new_weekly_dividends.append(ticker)
                            # print('Added ticker to weekly dividend list.')
                time.sleep(1)
            elif ticker_in_database(ticker):
                # if the ticker is in the database, do the same comparison to find the new upcoming weekly earnings
                ex_dividend_date = datetime.datetime.strptime(get_ex_dividend_date_DB(ticker)[0], "%Y-%m-%d").date()
                # print(ex_dividend_date)
                date_comp = datetime.datetime(ex_dividend_date.year, ex_dividend_date.month, ex_dividend_date.day)
                if not today <= date_comp <= one_week_from_now:
                    delete_ticker_from_database(conn, ticker)
                    new_weekly_dividends.append(ticker)

    # save the list of tickers with upcoming earnings to a json file for use in other scripts
    with open('StockTickers/weekly_dividends.json', 'w') as jsonfile:
        json.dump(new_weekly_dividends, jsonfile)

    conn.close()

def main():
	printDB()

if __name__ == "__main__":
    main()
