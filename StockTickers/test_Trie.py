import unittest
import csv
import pickle
import itertools

def generate_combinations(max_length):
    combinations = []
    for length in range(1, max_length + 1):
        for start_letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            for combo in itertools.combinations_with_replacement('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length):
                if start_letter in combo:
                    combinations.append(''.join(combo))
    return combinations

class TrieNode:
    def __init__(self):
        self.children = {}
        self.frequency = 0
class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert_with_frequency(self, word, frequency):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.frequency = frequency

    def search(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None  # Prefix not found
            node = node.children[char]
        return self._collect_tickers(node, prefix)

    def _collect_tickers(self, node, prefix):
        true_prefix_match = []
        next_highest_market_cap = []

        if node.frequency > 0:
            true_prefix_match.append((prefix, node.frequency))

        for char, child_node in node.children.items():
            child_prefix = prefix + char
            if child_node.frequency > 0:
                if child_prefix == prefix:  # Check for true prefix match
                    true_prefix_match.insert(0, (child_prefix, child_node.frequency))
                else:
                    next_highest_market_cap.extend(self._collect_tickers(child_node, child_prefix))
            else:
                next_highest_market_cap.extend(self._collect_tickers(child_node, child_prefix))

        # Sort next highest market cap tickers by market cap (ascending order)
        next_highest_market_cap.sort(key=lambda x: x[1], reverse=True)

        # Combine and return the lists (true prefix match + next highest market cap)
        return true_prefix_match + next_highest_market_cap[:4]

class TestTrie(unittest.TestCase):
    tickers_and_market_cap = []
    def setUp(self):
        combined_data = {}

        # Read tickers and market caps from NASDAQ file
        with open('StockTickers/nasdaq_tickers_cleaned.csv', 'r', newline='') as nasdaq_csv:
            reader = csv.DictReader(nasdaq_csv)
            for row in reader:
                ticker = row['Ticker']
                market_cap = int(row['Market Cap']) if row['Market Cap'] != 'N/A' else 0
                if market_cap == 0:
                    continue
                combined_data.setdefault(ticker, market_cap)

        # Read tickers and market caps from NYSE file
        with open('StockTickers/nyse_tickers_cleaned.csv', 'r', newline='') as nyse_csv:
            reader = csv.DictReader(nyse_csv)
            for row in reader:
                ticker = row['Ticker']
                market_cap = int(row['Market Cap']) if row['Market Cap'] != 'N/A' else 0
                if market_cap == 0:
                    continue
                combined_data.setdefault(ticker, market_cap)

        self.tickers_and_market_cap = list(combined_data.items())

        with open('FlaskApp/trie.pkl', 'rb') as f:
            self.trie = pickle.load(f)

    def test_trie(self):
        max_length = 5
        combinations = generate_combinations(max_length)
        for c in combinations:
            prefix = c
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