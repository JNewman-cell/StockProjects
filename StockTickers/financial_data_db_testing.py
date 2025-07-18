import yahoo_fin.stock_info as si

import pandas as pd
import yahoo_fin.stock_info as si
from typing import Dict, List, Optional, Any
from pathlib import Path

def find_year_index(columns, year):
        if str(year) in str(columns[i]):
            return i
    return None

def check_statement(ticker, statement, field):
    try:
        return statement.loc[field][0]
    except KeyError:
        print(f"{field} not found for {ticker}")
        return None


def extract_financial_data(ticker, years):
	data = {}
	print('Extracting Data for Ticker: '+ticker)

	for year in years:
		# Fetch financial data using yahoo_fin
		income_stmt = si.get_income_statement(ticker)
		cashflow = si.get_cash_flow(ticker)
		balance_sheet = si.get_balance_sheet(ticker)

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

def main():
	print(extract_financial_data('aapl', [2022]))