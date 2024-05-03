import csv
import time
import yfinance as yf

def get_market_cap(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get('marketCap', 'N/A')
    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return 'N/A'

def clean_tickers(input_file, output_file):
    start_time = time.time()

    with open(input_file, 'r') as f:
        tickers = {line.strip() for line in f if line.strip()}

    # Create a list to store ticker and market cap pairs
    ticker_market_cap_pairs = []

    for ticker in tickers:
        market_cap = get_market_cap(ticker)
        ticker_market_cap_pairs.append((ticker, market_cap))

    # Sort by ticker (optional)
    sorted_ticker_market_cap_pairs = sorted(ticker_market_cap_pairs, key=lambda x: x[0])

    end_time_read = time.time()

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ticker', 'Market Cap'])
        writer.writerows(sorted_ticker_market_cap_pairs)

    end_time_write = time.time()

    duration_read = (end_time_read - start_time) * 1000
    duration_write = (end_time_write - end_time_read) * 1000
    total_duration = (duration_read + duration_write)

    print(f"Reading tickers took {duration_read:.2f} milliseconds")
    print(f"Writing tickers with market cap took {duration_write:.2f} milliseconds")
    print(f"Total cleaning time: {total_duration:.2f} milliseconds")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_file = 'StockTickers/' + input_file.split('.')[0] + '_cleaned.csv'
    clean_tickers(input_file, output_file)
