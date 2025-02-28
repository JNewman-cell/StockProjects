import csv
import pickle
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../StockTickers'))
from csv_manipulation import extract_all_valid_tickers_and_market_caps_from_csvs

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

trie = Trie()

tickers = extract_all_valid_tickers_and_market_caps_from_csvs()

for ticker, frequency in tickers:
	trie.insert_with_frequency(ticker, int(float(frequency)))

# Save the Trie to a file
with open(os.getcwd()+'/trie.pkl', 'wb') as f:
    pickle.dump({'trie': trie}, f)
