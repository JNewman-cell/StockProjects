import csv

def extract_all_valid_tickers_from_csvs():
	"""
    Extract all the tickers from the file path of cleaned ticker csv files.

    Parameters:
	None

    Returns:
    list: all tickers that have financial data in the yahoo finance API.
    """
	tickers = []
	files = ['StockTickers/nasdaq_tickers_cleaned.csv', 'StockTickers/nyse_tickers_cleaned.csv']
	for file_path in files:
		with open(file_path, newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				frequency = row['Market Cap']
				if frequency != 'N/A':
					tickers.append(row['Ticker'])
	return tickers

def extract_all_valid_tickers_and_market_caps_from_csvs():
	"""
    Extract all the tickers from the file path of cleaned ticker csv files when creating the Trie.

    Parameters:
	None

    Returns:
    list: all tickers that have financial data in the yahoo finance API.
    """
	tickers = []
	files = ['../StockTickers/nasdaq_tickers_cleaned.csv', '../StockTickers/nyse_tickers_cleaned.csv']
	for file_path in files:
		with open(file_path, newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				frequency = row['Market Cap']
				if frequency != 'N/A':
					tickers.append((row['Ticker'],frequency))
	return tickers