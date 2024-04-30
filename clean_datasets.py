import csv
import time

def clean_tickers(input_file, output_file):
    start_time = time.time()

    # Use set comprehension to directly create a set of unique tickers
    with open(input_file, 'r') as f:
        tickers = {line.strip() for line in f if line.strip()}

    end_time_read = time.time()

    # Write unique tickers to new CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ticker'])
        writer.writerows([[ticker] for ticker in tickers])

    end_time_write = time.time()

    duration_read = end_time_read - start_time
    duration_write = end_time_write - end_time_read
    total_duration = duration_read + duration_write

    print(f"Reading tickers took {duration_read:.2f} seconds")
    print(f"Writing tickers took {duration_write:.2f} seconds")
    print(f"Total cleaning time: {total_duration:.2f} seconds")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_file = input_file.split('.')[0] + '_cleaned.csv'  # Create output file name
    clean_tickers(input_file, output_file)
