import datetime
import sys
import csv
import time
import os
import concurrent.futures
import yfinance as yf
from CRUD_earnings_database import update_earnings_db_and_weekly_earnings

def get_market_cap(ticker):
	"""
    Get the market cap of a company using its ticker symbol.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
   	tuple: The ticker and its market cap, N/A if market cap isnt found, meaning financial data is not in yahoo finance.
    """
	try:
		info = yf.Ticker(ticker).info
		return (ticker, info.get('marketCap', 'N/A'))
	except Exception as e:
		print(f"Error fetching market cap for {ticker}: {e}")
		return (ticker, 'N/A')

def fetch_market_caps(tickers, nonexistent_market_caps):
	"""
	Fetch all the market caps for the tickers that were pulled from the github repo.

	Parameters:
	tickers (list): The ticker symbols of the companies that were pulled.

	Returns:
	dict: The most recent quarterly earnings report of the company.
	"""
	market_caps = {}
	for ticker in tickers:
		if ticker not in nonexistent_market_caps:
			market_cap = get_market_cap(ticker)
			market_caps[ticker] = market_cap[1]
			time.sleep(0.2)
	return market_caps

def clean_tickers(input_file, output_file):
    """
    Create a cleaned csv file of all the tickers that were pulled from the github repo with their market caps, Columns: Ticker, Market Cap.

    Parameters:
    input_file (str): The name of the input txt file.
    output_file (str): The name of the output csv file.

    Returns:
    void
    """
    start_time = time.time()

    unnacounted_tickers = 0
    with open(input_file, 'r') as f:
        tickers = {line.strip() for line in f if line.strip()}

    end_time_read = time.time()

    nonexistent_market_caps = []
    # use this for later iterations to speed up fetching, removing tickers that aren't in yahoo finance database, every ticker is checked on Sunday.
    if os.path.exists(output_file):
        with open(output_file, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            nonexistent_market_caps = [row[0] for row in reader if row[1] == 'N/A']
    today = datetime.datetime.today().weekday()
    if today == 6:
        nonexistent_market_caps = []

    market_caps = fetch_market_caps(tickers, nonexistent_market_caps)
    market_caps.update({ticker: 'N/A' for ticker in nonexistent_market_caps})

    sorted_ticker_market_cap_pairs = sorted(market_caps.items(), key=lambda x: x[0])
    unnacounted_tickers = sum(1 for ticker, market_cap in market_caps.items() if market_cap == 'N/A')

    end_time_market_cap_fetching = time.time()

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ticker', 'Market Cap'])
        writer.writerows(sorted_ticker_market_cap_pairs)

    end_time_write = time.time()

    duration_read = (end_time_read - start_time) * 1000
    duration_market_cap_fetching = (end_time_market_cap_fetching - end_time_read)
    duration_write = (end_time_write - end_time_market_cap_fetching) * 1000
    total_duration = (duration_read + duration_market_cap_fetching + duration_write)

    print(f"Reading tickers took {duration_read:.2f} milliseconds")
    print(f"Fetching market caps took {duration_market_cap_fetching:.2f} seconds")
    print(f"Writing tickers with market cap took {duration_write:.2f} milliseconds")
    print(f"Total cleaning time: {total_duration:.2f} seconds")
    print("Number of N/A tickers: " + str(unnacounted_tickers))

def main():
	input_file = sys.argv[1]
	output_file = 'StockTickers/' + input_file.split('.')[0] + '_cleaned.csv'
	clean_tickers(input_file, output_file)
	update_earnings_db_and_weekly_earnings()

if __name__ == "__main__":
    main()