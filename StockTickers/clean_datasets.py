import datetime
import sys
import csv
import time
import os
import random
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf

def get_market_cap_batch(tickers):
    """
    Get market caps for multiple tickers in a single request.
    
    Parameters:
    tickers (list): List of ticker symbols.
    
    Returns:
    dict: Dictionary mapping tickers to their market caps.
    """
    try:
        # Download data for multiple tickers at once
        tickers_str = " ".join(tickers)
        data = yf.download(tickers_str, period="1d", group_by="ticker", progress=False)
        
        results = {}
        for ticker in tickers:
            try:
                # For single ticker download, the structure is different
                if len(tickers) == 1:
                    if not data.empty:
                        market_cap = yf.Ticker(ticker).info.get('marketCap', 'N/A')
                        results[ticker] = market_cap
                    else:
                        results[ticker] = 'N/A'
                else:
                    # Check if we have data for this ticker
                    if ticker in data.columns.levels[0] if hasattr(data.columns, 'levels') else False:
                        market_cap = yf.Ticker(ticker).info.get('marketCap', 'N/A')
                        results[ticker] = market_cap
                    else:
                        results[ticker] = 'N/A'
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                results[ticker] = 'N/A'
                
        return results
    except Exception as e:
        print(f"Batch download error: {e}")
        # Fallback to individual processing
        results = {}
        for ticker in tickers:
            try:
                market_cap = yf.Ticker(ticker).info.get('marketCap', 'N/A')
                results[ticker] = market_cap
            except:
                results[ticker] = 'N/A'
        return results

def fetch_market_caps_optimized(tickers, nonexistent_market_caps, batch_size=20, delay=1.0):
    """
    Optimized method to fetch market caps that balances speed with rate limit avoidance.
    
    Parameters:
    tickers (list): The ticker symbols to process.
    nonexistent_market_caps (list): Tickers known to not have market cap data.
    batch_size (int): Number of tickers to process in each batch.
    delay (float): Delay between batches in seconds.
    
    Returns:
    dict: Dictionary mapping tickers to their market caps.
    """
    market_caps = {}
    filtered_tickers = [t for t in tickers if t not in nonexistent_market_caps]
    
    # Special case for small number of tickers
    if len(filtered_tickers) <= batch_size:
        return get_market_cap_batch(filtered_tickers)
    
    # Process in batches
    for i in range(0, len(filtered_tickers), batch_size):
        batch = filtered_tickers[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(filtered_tickers) + batch_size - 1)//batch_size} ({len(batch)} tickers)")
        
        batch_results = get_market_cap_batch(batch)
        market_caps.update(batch_results)
        
        # Only delay if there are more batches
        if i + batch_size < len(filtered_tickers):
            time.sleep(delay)
    
    return market_caps

def clean_tickers(input_file, output_file, method='batch', batch_size=20, num_workers=1):
    """
    Create a cleaned csv file of all the tickers with their market caps.
    
    Parameters:
    input_file (str): The name of the input txt file.
    output_file (str): The name of the output csv file.
    method (str): The method to use - 'batch' or 'sequential'.
    """
    start_time = time.time()
    
    # Read tickers from file
    with open(input_file, 'r') as f:
        tickers = {line.strip() for line in f if line.strip()}
    
    print(f"Loaded {len(tickers)} unique tickers")
    end_time_read = time.time()
    
    # Load previously identified tickers without market cap data
    nonexistent_market_caps = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            nonexistent_market_caps = [row[0] for row in reader if len(row) >= 2 and row[1] == 'N/A']
        
        print(f"Loaded {len(nonexistent_market_caps)} tickers with known N/A market caps")
    
    # Reset cache on Sundays or if too many N/A values
    today = datetime.datetime.today().weekday()
    if today == 6 or len(nonexistent_market_caps) >= 500:
        nonexistent_market_caps = []
        print("Refreshing nonexistent market caps cache")
    
    # Choose fetching method based on parameter
    if method == 'batch':
        market_caps = fetch_market_caps_optimized(list(tickers), nonexistent_market_caps, batch_size=batch_size)
    else:  # sequential
        # Original method for reference
        market_caps = {}
        for ticker in tickers:
            if ticker not in nonexistent_market_caps:
                try:
                    info = yf.Ticker(ticker).info
                    market_caps[ticker] = info.get('marketCap', 'N/A')
                except Exception as e:
                    print(f"Error fetching market cap for {ticker}: {e}")
                    market_caps[ticker] = 'N/A'
                time.sleep(0.2)
    
    # Add back the nonexistent market caps
    for ticker in nonexistent_market_caps:
        market_caps[ticker] = 'N/A'
    
    # Sort by ticker symbol
    sorted_ticker_market_cap_pairs = sorted(market_caps.items(), key=lambda x: x[0])
    
    # Count tickers without market cap data
    unaccounted_tickers = sum(1 for _, market_cap in market_caps.items() if market_cap == 'N/A')
    
    end_time_market_cap_fetching = time.time()
    
    # Write results to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ticker', 'Market Cap'])
        writer.writerows(sorted_ticker_market_cap_pairs)
    
    end_time_write = time.time()
    
    # Calculate and print timing information
    duration_read = (end_time_read - start_time) * 1000
    duration_market_cap_fetching = end_time_market_cap_fetching - end_time_read
    duration_write = (end_time_write - end_time_market_cap_fetching) * 1000
    total_duration = (duration_read / 1000) + duration_market_cap_fetching + (duration_write / 1000)
    tickers_per_second = len(tickers) / duration_market_cap_fetching if duration_market_cap_fetching > 0 else 0
    
    print(f"Reading tickers took {duration_read:.2f} milliseconds")
    print(f"Fetching market caps took {duration_market_cap_fetching:.2f} seconds ({tickers_per_second:.2f} tickers/second)")
    print(f"Writing tickers with market cap took {duration_write:.2f} milliseconds")
    print(f"Total cleaning time: {total_duration:.2f} seconds")
    print(f"Number of N/A tickers: {unaccounted_tickers}")

def main():
    input_file = sys.argv[1]
    output_file = 'StockTickers/' + input_file.split('.')[0] + '_cleaned.csv'
    
    # Default to parallel method, but allow command line override
    method = 'parallel'
    if len(sys.argv) > 2:
        method = sys.argv[2]
    
    # You can adjust these parameters based on your observations
    batch_size = 20
    num_workers = 3
    
    clean_tickers(input_file, output_file, method=method, batch_size=batch_size, num_workers=num_workers)

if __name__ == "__main__":
    main()