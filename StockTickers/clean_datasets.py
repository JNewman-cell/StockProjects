import datetime
import sys
import csv
import time
import os
import concurrent.futures
import yfinance as yf
from random import uniform
from time import sleep
from tqdm import tqdm
import logging
from requests import Session
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data_fetch.log'),
        logging.StreamHandler()
    ]
)

def create_yf_session():
    """Create a session for yfinance to reuse."""
    session = Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    return session

def get_market_cap_with_retry(ticker, session, max_retries=3, base_delay=2):
    """
    Get the market cap of a company using its ticker symbol with retry logic.

    Parameters:
    ticker (str): The ticker symbol of the company.
    session: The requests session to use
    max_retries (int): Maximum number of retry attempts
    base_delay (int): Base delay between retries in seconds

    Returns:
    tuple: The ticker and its market cap, N/A if market cap isn't found
    """
    for attempt in range(max_retries):
        try:
            info = yf.Ticker(ticker, session=session).fast_info
            return (ticker, info.get('marketCap', 'N/A'))
        except Exception as e:
            if "Too Many Requests" in str(e):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + uniform(0, 1)
                    logging.info(f"Rate limited for {ticker}. Retrying in {delay:.2f} seconds...")
                    sleep(delay)
                    continue
            logging.error(f"Error fetching market cap for {ticker}: {e}")
            return (ticker, 'N/A')
    return (ticker, 'N/A')

def process_ticker_batch(tickers, session):
    """Process a batch of tickers using the same session."""
    results = {}
    for ticker in tickers:
        market_cap = get_market_cap_with_retry(ticker, session)
        results[ticker] = market_cap[1]
        sleep(uniform(1.0, 2.0))
    return results

def fetch_market_caps(tickers, nonexistent_market_caps):
    """
    Fetch all the market caps for the tickers that were pulled from the github repo.

    Parameters:
    tickers (list): The ticker symbols of the companies that were pulled.

    Returns:
    dict: Dictionary mapping tickers to their market caps
    """
    # Filter out nonexistent market caps
    tickers_to_fetch = [t for t in tickers if t not in nonexistent_market_caps]
    
    # Create batches of tickers (process 10 tickers per thread)
    batch_size = 10
    ticker_batches = [tickers_to_fetch[i:i + batch_size] 
                     for i in range(0, len(tickers_to_fetch), batch_size)]
    
    market_caps = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Create a session for each worker
        sessions = [create_yf_session() for _ in range(len(ticker_batches))]
        
        # Create futures for each batch
        future_to_batch = {
            executor.submit(process_ticker_batch, batch, session): batch 
            for batch, session in zip(ticker_batches, sessions)
        }
        
        # Process results with progress bar
        with tqdm(total=len(tickers_to_fetch), desc="Fetching market caps") as pbar:
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    market_caps.update(batch_results)
                    pbar.update(len(batch_results))
                except Exception as e:
                    logging.error(f"Batch processing failed: {e}")
                    
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
    if today == 6 or len(nonexistent_market_caps)>=500:
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

if __name__ == "__main__":
    main()