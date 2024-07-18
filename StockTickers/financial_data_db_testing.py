import sqlite3
import yfinance as yf
import pandas as pd
from collections import defaultdict
import csv
import time
import timeit
from datetime import datetime

tickers = []

def create_database():
    conn = sqlite3.connect('FlaskApp/financial_data.db')
    cursor = conn.cursor()

    # Create tables
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

def check_statement(ticker, statement, field):
	try:
		value = statement.loc[field].values[0]
	except Exception as e:
		if field != 'Stock Based Compensation' and field != 'EBITDA':
			print("An error occurred for field: "+field)
			if ticker not in errorsPerField[field]:
				errorsPerField[field].append(ticker)
		value = 0
	return value

def extract_financial_data(ticker, years):
	data = {}
	stock = yf.Ticker(ticker)

	income_stmt = stock.income_stmt
	cashflow = stock.cashflow
	balance_sheet = stock.balance_sheet
	print('Extracting Data for Ticker: '+ticker)

	def find_year_index(columns, year):
		for idx, col_name in enumerate(columns.astype(str)):
			if str(year) in col_name:
				return idx
		return None

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

def batch_insert_data(conn, ticker, data):
	cursor = conn.cursor()

	start_time = time.time()
	# Prepare a list of tuples to be inserted
	rows_to_insert = [(ticker, year, financials['Revenue'], financials['EBITDA'], financials['FCF'],
						financials['SBC'], financials['NetIncome'], financials['EPS'], financials['Cash'],
						financials['Debt'], financials['SharesOutstanding'])
						for year, financials in data.items()]

	print(rows_to_insert)

	# # Use executemany to insert all rows in a single operation
	# cursor.executemany('''INSERT OR IGNORE INTO stocks (ticker, year, revenue, ebitda, fcf, sbc, net_income, eps, cash, debt, shares_outstanding)
	# 						VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', rows_to_insert)
	
	conn.commit()

def data_exists(conn, ticker, year):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM stocks WHERE ticker = ? AND year = ?", (ticker, year))
    return cursor.fetchone() is not None

def insert_data_with_check(conn, ticker, data):
	cursor = conn.cursor()

	start_time = time.time()
	# Prepare a list of tuples to be inserted
	rows_to_insert = [(ticker, year, financials['Revenue'], financials['EBITDA'], financials['FCF'],
						financials['SBC'], financials['NetIncome'], financials['EPS'], financials['Cash'],
						financials['Debt'], financials['SharesOutstanding'])
						for year, financials in data.items()]

	# Insert each row individually, checking for existence first
	for row in rows_to_insert:
		if not data_exists(conn, row[0], row[1]):
			cursor.execute('''INSERT INTO stocks (ticker, year, revenue, ebitda, fcf, sbc, net_income, eps, cash, debt, shares_outstanding)
								VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)
	end_time = time.time()

	print(f"Time taken for insert with check: {end_time - start_time} seconds")

	conn.commit()

def main():
	# Create database and get connection
	conn = create_database()

	# create list of years to search for in financial statements
	current_year = datetime.now().year
	year_range = list(range(2020, current_year+1))

	# test ticker set
	tickers = ['AAPL', 'GOOGL', 'EA']

	for ticker in tickers:
		data = extract_financial_data(ticker, year_range)

		batch_insert_data(conn, ticker, data)
		
	conn.close()

if __name__ == "__main__":
    main()
