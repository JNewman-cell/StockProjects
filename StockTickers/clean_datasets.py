import csv
import time
import os
import concurrent.futures
import yfinance as yf

def get_market_cap(ticker):
    try:
        info = yf.Ticker(ticker).info
        return (ticker, info.get('marketCap', 'N/A'))
    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return (ticker, 'N/A')

def fetch_market_caps(tickers, nonexistent_market_caps):
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(get_market_cap, ticker): ticker for ticker in tickers if ticker not in nonexistent_market_caps}
        market_caps = {}
        for future in concurrent.futures.as_completed(futures):
            ticker = futures[future]
            market_caps[ticker] = future.result()[1]
    return market_caps

def clean_tickers(input_file, output_file):
	start_time = time.time()

	with open(input_file, 'r') as f:
	    tickers = {line.strip() for line in f if line.strip()}

	end_time_read = time.time()

	nonexistent_market_caps = []
	# use this for later iterations to speed up fetching, removing tickers that aren't in database
	# if os.path.exists(output_file):
	#     with open(output_file, 'r') as csvfile:
	#         reader = csv.reader(csvfile)
	#         next(reader)
	#         nonexistent_market_caps = [row[0] for row in reader if row[1] == 'N/A']

	print(nonexistent_market_caps)

	# Use fetch_market_caps to fetch market caps in parallel
	market_caps = fetch_market_caps(tickers, nonexistent_market_caps)
	market_caps.update({ticker: 'N/A' for ticker in nonexistent_market_caps})

	sorted_ticker_market_cap_pairs = sorted(market_caps.items(), key=lambda x: x[0])

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
	print(f"Total cleaning time: {total_duration:.2f} milliseconds")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_file = 'StockTickers/' + input_file.split('.')[0] + '_cleaned.csv'
    clean_tickers(input_file, output_file)
