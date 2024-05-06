from flask import Flask, render_template, request, jsonify
import pickle

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
		return true_prefix_match + next_highest_market_cap[:9]

# Load the Trie in your Flask app
with open('FlaskApp/trie.pkl', 'rb') as f:
    trie = pickle.load(f)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    prefix = request.args.get('prefix', '')
    results = trie.search(prefix.upper())
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
