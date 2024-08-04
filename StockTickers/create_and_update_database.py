import sqlite3
import yfinance as yf
import pandas as pd
from collections import defaultdict
from csv_manipulation import extract_all_valid_tickers_from_csvs
from CRUD_earnings_database import get_tickers_with_earnings_within_a_week
import time
from datetime import datetime

def find_year_index(columns, year):
	for idx, col_name in enumerate(columns.astype(str)):
		if str(year) in col_name:
			return idx
	return None

def extract_financial_data(ticker, years):
	"""
    Extract the yearly financial data of a ticker for the amount of years since 2020.

    Parameters:
    ticker (str): The ticker symbol of the company.
	years (list): The years that we are extracting data for.

    Returns:
    dict: holding each years data, encoded with the year they were taken from
    """
	data = {}
	stock = yf.Ticker(ticker)

	income_stmt = stock.income_stmt
	cashflow = stock.cashflow
	balance_sheet = stock.balance_sheet
	print('Extracting Data for Ticker: '+ticker)

	for year in years:
		index_of_year_income = find_year_index(income_stmt.columns, year)
		index_of_year_cashflow = find_year_index(cashflow.columns, year)
		index_of_year_balance_sheet = find_year_index(balance_sheet.columns, year)

		# only want years where all data is found, some new data has blanks in certain sheets
		if index_of_year_income == None or index_of_year_balance_sheet == None or index_of_year_cashflow == None:
			print('skipped year: ' + str(year))
			continue

		# Filter data for the specific year
		income_stmt_year = income_stmt.iloc[:,index_of_year_income:index_of_year_income+1]
		cashflow_year = cashflow.iloc[:,index_of_year_cashflow:index_of_year_cashflow+1]
		balance_sheet_year = balance_sheet.iloc[:,index_of_year_balance_sheet:index_of_year_balance_sheet+1]
		
		# Extract data
		financials = {
			'Revenue': check_statement(ticker, income_stmt_year, 'Total Revenue'),
			'EBITDA': check_statement(ticker, income_stmt_year, 'EBITDA'),
			'FCF': check_statement(ticker, cashflow_year, 'Free Cash Flow'),
			'SBC': check_statement(ticker, cashflow_year, 'Stock Based Compensation'),
			'NetIncome': check_statement(ticker, income_stmt_year, 'Net Income'),
			'EPS': check_statement(ticker, income_stmt_year, 'Diluted EPS'),
			'Cash': check_statement(ticker, balance_sheet_year, 'Cash And Cash Equivalents'),
			'Debt': check_statement(ticker, balance_sheet_year, 'Total Debt'),
			'SharesOutstanding': check_statement(ticker, balance_sheet_year, 'Ordinary Shares Number')
		}
		
		data[year] = financials
	return data

def check_statement(ticker, statement, field):
	try:
		value = statement.loc[field].values[0]
	except Exception as e:
		value = 0
	return value

def create_database():
	"""
    Creates the database for the yearly financials of each company.

    Parameters:
	None

    Returns:
    sqlite3.conn: connection to the yearly financial database.
    """
	conn = sqlite3.connect('FlaskApp/financial_data.db')
	cursor = conn.cursor()

	cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
						id INTEGER PRIMARY KEY,
						ticker TEXT NOT NULL,
						year INTEGER NOT NULL,
						revenue REAL,
						ebitda REAL,
						fcf REAL,
						sbc REAL,
						net_income REAL,
						eps REAL,
						cash REAL,
						debt REAL,
						shares_outstanding REAL,
						UNIQUE (ticker, year)
					)''')

	conn.commit()
	return conn

def insert_data_into_database(conn, ticker, data):
	cursor = conn.cursor()

	# Prepare a list of tuples to be inserted
	rows_to_insert = [(ticker, year, financials['Revenue'], financials['EBITDA'], financials['FCF'],
						financials['SBC'], financials['NetIncome'], financials['EPS'], financials['Cash'],
						financials['Debt'], financials['SharesOutstanding'])
						for year, financials in data.items()]

	# Use executemany to insert all rows in a single operation
	cursor.executemany('''INSERT OR IGNORE INTO stocks (ticker, year, revenue, ebitda, fcf, sbc, net_income, eps, cash, debt, shares_outstanding)
							VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', rows_to_insert)

	conn.commit()

# prints out the entire database for debugging
def printDB():
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('FlaskApp/financial_data.db')
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
	conn = create_database()

	tickers_to_check = get_tickers_with_earnings_within_a_week()

	# create list of years to search for in financial statements
	current_year = datetime.now().year
	year_range = list(range(2020, current_year+1))
	# print(year_range)

	# test ticker set
	# tickers = ['AAPL', 'GOOGL']
	# tickers = ['EA']
	# print(len(tickers))

	for ticker in tickers_to_check:
		data = extract_financial_data(ticker, year_range)
		insert_data_into_database(conn, ticker, data)
		# sleep to prevent API rate limit trigger
		time.sleep(1)
	conn.close()

	# Uncomment the following line if you want to print the database contents
	# print(errorsPerField)
	# printDB()

if __name__ == "__main__":
    main()
