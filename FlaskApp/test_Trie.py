import unittest
import csv
import pickle
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from create_Trie import Trie, TrieNode

class TestTrieBase(unittest.TestCase):
    """Base class for Trie tests with common setup and utility methods."""
    
    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures that can be reused across test methods."""
        cls.data_dir = Path('../StockTickers')
        cls.trie_path = Path(os.getcwd()) / 'trie.pkl'
        cls.tickers_and_market_cap = cls._load_ticker_data()
        cls.trie = cls._load_trie()

    @classmethod
    def _load_ticker_data(cls) -> List[Tuple[str, int]]:
        """Load and combine ticker data from NASDAQ and NYSE files.
        
        Returns:
            List of tuples containing ticker symbols and their market caps.
        """
        combined_data: Dict[str, int] = {}
        
        # Define file paths
        nasdaq_file = cls.data_dir / 'nasdaq_tickers_cleaned.csv'
        nyse_file = cls.data_dir / 'nyse_tickers_cleaned.csv'
        
        for file_path in [nasdaq_file, nyse_file]:
            if not file_path.exists():
                raise FileNotFoundError(f"Required data file not found: {file_path}")
                
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        market_cap = int(row['Market Cap']) if row['Market Cap'] != 'N/A' else 0
                        if market_cap > 0:  # Only include tickers with valid market cap
                            combined_data[row['Ticker']] = market_cap
                    except (ValueError, KeyError) as e:
                        print(f"Error processing row in {file_path.name}: {row}. Error: {e}")
        
        return list(combined_data.items())

    @classmethod
    def _load_trie(cls) -> Trie:
        """Load the Trie structure from pickle file.
        
        Returns:
            Loaded Trie object.
            
        Raises:
            FileNotFoundError: If trie.pkl doesn't exist
            pickle.UnpicklingError: If pickle file is corrupted
        """
        if not cls.trie_path.exists():
            raise FileNotFoundError(f"Trie data file not found: {cls.trie_path}")
            
        with open(cls.trie_path, 'rb') as f:
            try:
                data = pickle.load(f)
                return data['trie']
            except (pickle.UnpicklingError, KeyError) as e:
                raise RuntimeError(f"Error loading Trie data: {e}")

    def generate_test_combinations(self, max_length: int = 5) -> Set[str]:
        """Generate test combinations for Trie search.
        
        Args:
            max_length: Maximum length of combinations to generate.
            
        Returns:
            Set of string combinations for testing.
        """
        combinations = set()
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        for length in range(1, max_length + 1):
            for start_letter in letters:
                for combo in itertools.combinations_with_replacement(letters, length):
                    if start_letter in combo:
                        combinations.add(''.join(combo))
        return combinations

class TestTrieSearching(TestTrieBase):
    """Test cases for Trie search functionality."""

    def test_empty_search(self):
        """Test searching with empty string."""
        result = self.trie.search("")
        self.assertIsNone(result, "Empty string search should return None")

    def test_invalid_input(self):
        """Test searching with invalid input."""
        invalid_inputs = [None, 123, "$ABC", "abc"]  # lowercase, numbers, special chars
        for input_val in invalid_inputs:
            with self.subTest(input_val=input_val):
                with self.assertRaises((TypeError, ValueError)):
                    self.trie.search(input_val)

    def test_exact_matches(self):
        """Test searching for exact ticker matches."""
        # Test some known tickers
        known_tickers = ["AAPL", "MSFT", "GOOGL"]
        for ticker in known_tickers:
            with self.subTest(ticker=ticker):
                result = self.trie.search(ticker)
                self.assertIsNotNone(result, f"Should find exact match for {ticker}")
                self.assertTrue(any(t[0] == ticker for t in result),
                              f"Result should contain exact match {ticker}")

    def test_prefix_search(self):
        """Test searching with valid ticker prefixes."""
        test_cases = [
            ("A", 4),    # Should return top 4 tickers starting with A
            ("AA", 4),   # Should return top 4 tickers starting with AA
            ("AAP", 4)   # Should return top 4 tickers starting with AAP
        ]
        
        for prefix, expected_count in test_cases:
            with self.subTest(prefix=prefix):
                result = self.trie.search(prefix)
                self.assertIsNotNone(result, f"Should find matches for prefix {prefix}")
                self.assertLessEqual(len(result), expected_count,
                                   f"Should return at most {expected_count} results")
                for ticker, _ in result:
                    self.assertTrue(ticker.startswith(prefix),
                                  f"All results should start with {prefix}")

    def test_market_cap_ordering(self):
        """Test that results are ordered by market cap."""
        for prefix in ["A", "B", "C"]:
            with self.subTest(prefix=prefix):
                result = self.trie.search(prefix)
                if result:
                    market_caps = [mc for _, mc in result]
                    self.assertEqual(market_caps, sorted(market_caps, reverse=True),
                                  "Results should be ordered by descending market cap")

    def test_comprehensive_search(self):
        """Test Trie search with comprehensive combination of inputs."""
        combinations = self.generate_test_combinations(max_length=3)  # Reduced for faster testing
        
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_prefix = {
                executor.submit(self._run_search_test, prefix): prefix 
                for prefix in combinations
            }
            
            for future in as_completed(future_to_prefix):
                prefix = future_to_prefix[future]
                try:
                    future.result()
                except Exception as e:
                    self.fail(f"Test failed for prefix '{prefix}': {e}")

    def _run_search_test(self, prefix: str) -> None:
        """Run a single search test case.
        
        Args:
            prefix: The prefix to search for.
            
        Raises:
            AssertionError: If the test case fails.
        """
        expected = self._get_expected_results(prefix)
        actual = self.trie.search(prefix)
        
        if expected is None:
            self.assertIsNone(actual, f"Expected None for prefix '{prefix}'")
        else:
            self.assertEqual(
                actual, expected,
                f"Incorrect results for prefix '{prefix}'\n"
                f"Expected: {expected}\n"
                f"Actual: {actual}"
            )

    def _get_expected_results(self, prefix: str) -> Optional[List[Tuple[str, int]]]:
        """Calculate expected search results for a prefix.
        
        Args:
            prefix: The prefix to search for.
            
        Returns:
            List of expected matches or None if no matches expected.
        """
        exact_matches = []
        prefix_matches = []
        
        for ticker, market_cap in self.tickers_and_market_cap:
            if ticker == prefix:
                exact_matches.append((ticker, market_cap))
            elif ticker.startswith(prefix) and ticker != prefix:
                prefix_matches.append((ticker, market_cap))

        # Sort prefix matches by market cap
        prefix_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Combine results: exact matches first, then top prefix matches
        results = exact_matches + prefix_matches[:4]
        
        return results if results else None

if __name__ == '__main__':
    unittest.main(verbosity=2)
