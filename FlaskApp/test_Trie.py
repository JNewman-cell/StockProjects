import unittest
import csv
import pickle
import itertools
from concurrent.futures import ThreadPoolExecutor
import os
from create_Trie import Trie, TrieNode

def generate_combinations(max_length):
    combinations = []
    for length in range(1, max_length + 1):
        for start_letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            for combo in itertools.combinations_with_replacement('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length):
                if start_letter in combo:
                    combinations.append(''.join(combo))
    return combinations

class TestTrie(unittest.TestCase):
    tickers_and_market_cap = []

    def setUp(self):
        combined_data = {}

        # Read tickers and market caps from NASDAQ file
        with open('../StockTickers/nasdaq_tickers_cleaned.csv', 'r', newline='') as nasdaq_csv:
            reader = csv.DictReader(nasdaq_csv)
            for row in reader:
                ticker = row['Ticker']
                market_cap = int(row['Market Cap']) if row['Market Cap'] != 'N/A' else 0
                if market_cap == 0:
                    continue
                combined_data.setdefault(ticker, market_cap)

        # Read tickers and market caps from NYSE file
        with open('../StockTickers/nyse_tickers_cleaned.csv', 'r', newline='') as nyse_csv:
            reader = csv.DictReader(nyse_csv)
            for row in reader:
                ticker = row['Ticker']
                market_cap = int(row['Market Cap']) if row['Market Cap'] != 'N/A' else 0
                if market_cap == 0:
                    continue
                combined_data.setdefault(ticker, market_cap)

        self.tickers_and_market_cap = list(combined_data.items())

        with open(os.getcwd()+'/trie.pkl', 'rb') as f:
            data = pickle.load(f)
            self.trie = data['trie']

    def test_trie(self):
        max_length = 5
        combinations = generate_combinations(max_length)
        
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(self.run_test_case, combinations))
        
        for result in results:
            self.assertIsNone(result)

    def run_test_case(self, prefix):
        expected = self.get_expected_tickers(prefix)
        result = self.trie.search(prefix)
        self.assertEqual(result, expected, f"Incorrect result for prefix '{prefix}'")

    def get_expected_tickers(self, prefix):
        expected = []
        prefixes = []
        
        for ticker, market_cap in self.tickers_and_market_cap:
            if ticker == prefix and market_cap != 0:
                expected.append((ticker, market_cap))
            elif ticker.startswith(prefix) and ticker != prefix:
                prefixes.append((ticker, market_cap))

        prefixes.sort(key=lambda x: x[1], reverse=True)

        result = [t for t in prefixes[:4]]
        for ticker, market_cap in result:
            expected.append((ticker, market_cap))

        if not expected:
            return None
        else:
            return expected

if __name__ == '__main__':
    unittest.main()
