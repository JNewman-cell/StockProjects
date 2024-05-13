import sqlite3
import yfinance as yf
import pandas as pd
from collections import defaultdict
import csv
import time
from datetime import datetime

tickers = []

def extract_tickers_from_csv(file_path):
	with open(file_path, newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			frequency = row['Market Cap']
			if frequency != 'N/A':
				tickers.append(row['Ticker'])
	return tickers

def data_exists_in_database(conn, ticker, year_range):
    cursor = conn.cursor()
    for year in year_range:
        cursor.execute('''SELECT 1 FROM stocks WHERE ticker = ? AND year = ?''', (ticker, year))
        if cursor.fetchone() is None:
            return False
    return True

def extract_financial_data(ticker, year):
	data = {}
	stock = yf.Ticker(ticker)

	income_stmt = stock.income_stmt
	cashflow = stock.cashflow
	balance_sheet = stock.balance_sheet
	print(ticker)

	for year in years:
		income_stmt_columns_as_strings = income_stmt.columns.astype(str)
		index_of_year_income = None
		for idx, col_name in enumerate(income_stmt_columns_as_strings):
			if str(year) in col_name:
				index_of_year_income = idx
				break
				
		# Check cash flow statement
		cashflow_columns_as_strings = cashflow.columns.astype(str)
		index_of_year_cashflow = None
		for idx, col_name in enumerate(cashflow_columns_as_strings):
			if str(year) in col_name:
				index_of_year_cashflow = idx
				break
		
		# Check balance sheet statement
		balance_sheet_columns_as_strings = balance_sheet.columns.astype(str)
		index_of_year_balance_sheet = None
		for idx, col_name in enumerate(balance_sheet_columns_as_strings):
			if str(year) in col_name:
				index_of_year_balance_sheet = idx
				break

		index_of_year = None
		if index_of_year_income == index_of_year_cashflow == index_of_year_balance_sheet:
			index_of_year = index_of_year_income

		if index_of_year == None:
			continue

		start,end = index_of_year, index_of_year+1

		# Filter data for the specific year
		income_stmt_year = income_stmt.iloc[:,start:end]
		cashflow_year = cashflow.iloc[:,start:end]
		balance_sheet_year = balance_sheet.iloc[:,start:end]
		
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

errorsPerField = {
	'Total Revenue':[],
	'Free Cash Flow':[],
	'Net Income':[],
	'Diluted EPS':[],
	'Cash And Cash Equivalents':[],
	'Total Debt':[],
	'Ordinary Shares Number':[],
}

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

def insert_data_into_database(conn, ticker, data):
    cursor = conn.cursor()

    for year, financials in data.items():
        cursor.execute('''INSERT OR IGNORE INTO stocks (ticker, year, revenue, ebitda, fcf, sbc, net_income, eps, cash, debt, shares_outstanding)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (ticker, year, financials['Revenue'], financials['EBITDA'], financials['FCF'],
                        financials['SBC'], financials['NetIncome'], financials['EPS'], financials['Cash'],
                        financials['Debt'], financials['SharesOutstanding']))

    conn.commit()

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
	conn = sqlite3.connect('FlaskApp/financial_data.db')

	# Get the tickers from the data
	csv_file_path = 'StockTickers/nasdaq_tickers_cleaned.csv'
	csv_file_path2 = 'StockTickers/nyse_tickers_cleaned.csv'
	extract_tickers_from_csv(csv_file_path)
	extract_tickers_from_csv(csv_file_path2)
	
	# create list of years to search for in financial statements
	current_year = datetime.now().year
	year_range = list(range(2020, current_year+1))
	# print(year_range)

	# test ticker set
	# tickers = ['AAPL', 'GOOGL']
	# print(len(tickers))

	for ticker in tickers:
		for year in years:
			if not data_exists_in_database(conn, ticker, year_range):
				data = extract_financial_data(ticker, year_range)
				insert_data_into_database(conn, ticker, data)
	conn.close()

	# print(errorsPerField)
	
	# printDB()

if __name__ == "__main__":
    main()
