import sqlite3
import datetime
import time
import os
import logging
import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from tqdm import tqdm
from yahooquery import Ticker

from csv_manipulation import extract_all_valid_tickers_from_csvs
from CRUD_earnings_database import get_tickers_with_earnings_within_a_week

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_year_index(columns, year):
	"""
    Finds the index of the year in the yearly earnings dataframe.

    Parameters:
    columns (list): The head columns of the earnings dataframe.
	year (int): The year that we are trying to extract data for.

    Returns:
    idx: The index of the year in the columns, None if not found
    """
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
    dict: Holding each years data, encoded with the year they were taken from
    """
	data = {}
	try:
		stock = Ticker(ticker, timeout=30)
		
		# Get all required data at once
		income_stmt = stock.income_statement(frequency='a')
		cashflow = stock.cash_flow(frequency='a')
		balance = stock.balance_sheet(frequency='a')
		
		# Process each year's data
		for year in years:
			year_data = {}
			try:
				# Filter for the specific year
				year_income = income_stmt[income_stmt['asOfDate'].dt.year == year] if isinstance(income_stmt, pd.DataFrame) else None
				year_cashflow = cashflow[cashflow['asOfDate'].dt.year == year] if isinstance(cashflow, pd.DataFrame) else None
				year_balance = balance[balance['asOfDate'].dt.year == year] if isinstance(balance, pd.DataFrame) else None
				
				if year_income is not None and not year_income.empty:
					year_data.update({
						'Revenue': year_income['TotalRevenue'].iloc[0] if 'TotalRevenue' in year_income else None,
						'EBITDA': year_income['EBITDA'].iloc[0] if 'EBITDA' in year_income else None,
						'NetIncome': year_income['NetIncome'].iloc[0] if 'NetIncome' in year_income else None,
						'EPS': year_income['DilutedEPS'].iloc[0] if 'DilutedEPS' in year_income else None
					})
				
				if year_cashflow is not None and not year_cashflow.empty:
					year_data.update({
						'FCF': year_cashflow['FreeCashFlow'].iloc[0] if 'FreeCashFlow' in year_cashflow else None,
						'SBC': year_cashflow['StockBasedCompensation'].iloc[0] if 'StockBasedCompensation' in year_cashflow else None
					})
				
				if year_balance is not None and not year_balance.empty:
					year_data.update({
						'Cash': year_balance['CashAndCashEquivalents'].iloc[0] if 'CashAndCashEquivalents' in year_balance else None,
						'Debt': year_balance['TotalDebt'].iloc[0] if 'TotalDebt' in year_balance else None,
						'SharesOutstanding': year_balance['ShareIssued'].iloc[0] if 'ShareIssued' in year_balance else None
					})
				
				if year_data:  # Only add if we got some data
					data[year] = year_data
					
			except Exception as e:
				print(f"Error processing year {year} for {ticker}: {e}")
				continue
				
	except Exception as e:
		print(f"Error fetching data for {ticker}: {e}")
		
	return data

def create_database():
	"""
    Creates the database for the yearly financials of each company.

    Parameters:
	None

    Returns:
    sqlite3.conn: Connection to the yearly financial database.
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
	"""
    Insert the yearly financial data into the database.

    Parameters:
	conn (sqlite3.conn): The connection to the yearly financial database.
    ticker (str): The ticker symbol of the company.
	data (dict): The yearly financial data for the given years.

    Returns:
    None
    """
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
	"""
    Prints out the entire database for the yearly financials of each company.

    Parameters:
	None

    Returns:
    None
    """
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

	# check cached tickers
	tickers = get_tickers_with_earnings_within_a_week()
	# # check all tickers
	# tickers_to_check = extract_all_valid_tickers_from_csvs()

	# create list of years to search for in financial statements
	current_year = datetime.now().year
	year_range = list(range(2020, current_year+1))
	# print(year_range)

	# test ticker set
	# tickers = ['AAPL', 'GOOGL']
	# tickers = ['EA']
	# print(len(tickers))

	for ticker in tqdm(tickers, desc="Updating financials database"):
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
