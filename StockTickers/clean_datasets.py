import csv
import time


def clean_tickers(input_file, output_file):
    start_time = time.time()

    with open(input_file, 'r') as f:
        tickers = {line.strip() for line in f if line.strip()}
    
    sorted_tickers = sorted(tickers)

    end_time_read = time.time()

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ticker'])
        writer.writerows([[ticker] for ticker in sorted_tickers])

    end_time_write = time.time()

    duration_read = (end_time_read - start_time) * 1000
    duration_write = (end_time_write - end_time_read) * 1000
    total_duration = (duration_read + duration_write)

    print(f"Reading tickers took {duration_read:.2f} milliseconds")
    print(f"Writing tickers took {duration_write:.2f} milliseconds")
    print(f"Total cleaning time: {total_duration:.2f} milliseconds")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_file = '../StockTickers/' + input_file.split('.')[0] + '_cleaned.csv'
    clean_tickers(input_file, output_file)
