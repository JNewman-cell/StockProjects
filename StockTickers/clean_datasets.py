import datetime
import sys
import csv
import time
import os
from yahooquery import Ticker
from tqdm import tqdm
import logging
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data_fetch.log'),
        logging.StreamHandler()
    ]
)

def fetch_market_caps(tickers, nonexistent_market_caps):
    """
    Fetch all the market caps for the tickers using yahooquery.

    Parameters:
    tickers (list): The ticker symbols of the companies.
    nonexistent_market_caps (list): List of tickers known to not have market caps.

    Returns:
    dict: Dictionary mapping tickers to their market caps
    """
    # Filter out known nonexistent market caps
    tickers_to_fetch = [t for t in tickers if t not in nonexistent_market_caps]
    
    if not tickers_to_fetch:
        return {ticker: 'N/A' for ticker in nonexistent_market_caps}

    logging.info(f"Fetching market caps for {len(tickers_to_fetch)} tickers...")
    market_caps = {}
    
    try:
        # Initialize Ticker with all symbols at once for batch processing
        ticker_data = Ticker(tickers_to_fetch, timeout=30)
        
        # Get all market caps in one batch request
        quotes = ticker_data.price

        # Process results
        for ticker in tqdm(tickers_to_fetch, desc="Fetching market caps", unit="ticker"):
            try:
                if isinstance(quotes, dict) and ticker in quotes:
                    ticker_info = quotes[ticker]
                    if isinstance(ticker_info, dict) and 'marketCap' in ticker_info:
                        market_caps[ticker] = ticker_info['marketCap']
                        logging.info(f"Successfully fetched market cap for {ticker}")
                    else:
                        market_caps[ticker] = 'N/A'
                        logging.error(f"No market cap data for {ticker}")
                else:
                    market_caps[ticker] = 'N/A'
                    logging.error(f"No data found for {ticker}")
            except Exception as e:
                logging.error(f"Error processing market cap for {ticker}: {e}")
                market_caps[ticker] = 'N/A'
                
    except Exception as e:
        logging.error(f"Batch processing failed: {e}")
        # If batch fails, mark all remaining tickers as N/A
        for ticker in tickers_to_fetch:
            if ticker not in market_caps:
                market_caps[ticker] = 'N/A'
    
    # Add back the known nonexistent market caps
    market_caps.update({ticker: 'N/A' for ticker in nonexistent_market_caps})
    return market_caps

def clean_tickers(input_file, output_file):
    """
    Create a cleaned csv file of all the tickers with their market caps.

    Parameters:
    input_file (str): The name of the input txt file.
    output_file (str): The name of the output csv file.
    """
    start_time = time.time()

    # Read and clean tickers
    with open(input_file, 'r') as f:
        tickers = {line.strip() for line in f if line.strip()}

    end_time_read = time.time()

    # Handle nonexistent market caps
    nonexistent_market_caps = []
    if os.path.exists(output_file):
        try:
            df = pd.read_csv(output_file)
            nonexistent_market_caps = df[df['Market Cap'] == 'N/A']['Ticker'].tolist()
        except Exception as e:
            logging.error(f"Error reading existing file: {e}")
            nonexistent_market_caps = []

    # Reset nonexistent_market_caps on Sundays or if too many N/A values
    today = datetime.datetime.today().weekday()
    if today == 6 or len(nonexistent_market_caps) >= 500:
        nonexistent_market_caps = []

    # Fetch market caps
    market_caps = fetch_market_caps(tickers, nonexistent_market_caps)
    market_caps.update({ticker: 'N/A' for ticker in nonexistent_market_caps})

    sorted_ticker_market_cap_pairs = sorted(market_caps.items(), key=lambda x: x[0])
    unnacounted_tickers = sum(1 for ticker, market_cap in market_caps.items() if market_cap == 'N/A')

    end_time_market_cap_fetching = time.time()

    # Write results to file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ticker', 'Market Cap'])
        writer.writerows(sorted_ticker_market_cap_pairs)

    end_time_write = time.time()

    # Calculate and print timing information
    duration_read = (end_time_read - start_time) * 1000
    duration_market_cap_fetching = (end_time_market_cap_fetching - end_time_read)
    duration_write = (end_time_write - end_time_market_cap_fetching) * 1000
    total_duration = (duration_read + duration_market_cap_fetching + duration_write)

    print(f"Reading tickers took {duration_read:.2f} milliseconds")
    print(f"Fetching market caps took {duration_market_cap_fetching:.2f} seconds")
    print(f"Writing tickers with market cap took {duration_write:.2f} milliseconds")
    print(f"Total cleaning time: {total_duration:.2f} seconds")
    print(f"Number of N/A tickers: {unnacounted_tickers}")

def main():
    input_file = sys.argv[1]
    output_file = 'StockTickers/' + input_file.split('.')[0] + '_cleaned.csv'
    clean_tickers(input_file, output_file)

if __name__ == "__main__":
    main()