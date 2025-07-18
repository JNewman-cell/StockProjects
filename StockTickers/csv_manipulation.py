import csv
import os
import logging
from typing import List, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_all_valid_tickers_from_csvs() -> List[str]:
	"""
    Extract all the tickers from the file path of cleaned ticker csv files.

    Parameters:
	None

    Returns:
    list: all tickers that have financial data in the yahoo finance API.
    """
	tickers = []
	current_dir = os.path.dirname(os.path.abspath(__file__))
	files = [
		os.path.join(current_dir, 'nasdaq_tickers_cleaned.csv'),
		os.path.join(current_dir, 'nyse_tickers_cleaned.csv')
	]
	for file_path in files:
		if not os.path.exists(file_path):
			logger.error(f"File not found: {file_path}")
			continue
		with open(file_path, newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				frequency = row['Market Cap']
				if frequency != 'N/A':
					tickers.append(row['Ticker'])
	return tickers

def extract_all_valid_tickers_and_market_caps_from_csvs() -> List[Tuple[str, Union[str, float]]]:
	"""
    Extract all the tickers from the file path of cleaned ticker csv files when creating the Trie.

    Returns:
        List[Tuple[str, Union[str, float]]]: List of tuples containing (ticker, market_cap) pairs
            where market_cap can be either a string or float value.
    """
	tickers = []
	current_dir = os.path.dirname(os.path.abspath(__file__))
	files = [
		os.path.join(current_dir, 'nasdaq_tickers_cleaned.csv'),
		os.path.join(current_dir, 'nyse_tickers_cleaned.csv')
	]
	for file_path in files:
		if not os.path.exists(file_path):
			logger.error(f"File not found: {file_path}")
			continue
		with open(file_path, newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				frequency = row['Market Cap']
				if frequency != 'N/A':
					tickers.append((row['Ticker'],frequency))
	return tickers