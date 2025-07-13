"""
Trie implementation for efficient ticker symbol lookups.

This module implements a Trie data structure optimized for storing and retrieving
stock ticker symbols with their market caps. It provides fast prefix-based searches
and returns results ordered by market capitalization.
"""

import csv
import pickle
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import logging
from contextlib import contextmanager

sys.path.append(os.path.join(os.path.dirname(__file__), '../StockTickers'))
from csv_manipulation import extract_all_valid_tickers_and_market_caps_from_csvs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_RESULTS = 4
PICKLE_FILE = 'trie.pkl'

@dataclass
class TrieNode:
    """Node in the Trie structure.
    
    Attributes:
        children: Dictionary mapping characters to child nodes
        market_cap: Market capitalization value for the ticker (if it's a terminal node)
        is_terminal: Whether this node represents the end of a ticker symbol
    """
    children: Dict[str, 'TrieNode']
    market_cap: int
    is_terminal: bool

    def __init__(self):
        """Initialize an empty Trie node."""
        self.children = {}
        self.market_cap = 0
        self.is_terminal = False

class TrieError(Exception):
    """Base exception for Trie-related errors."""
    pass

class InvalidTickerError(TrieError):
    """Raised when an invalid ticker symbol is provided."""
    pass

class Trie:
    """Trie data structure for efficient ticker symbol lookups.
    
    This implementation is optimized for storing stock ticker symbols and their
    market capitalizations, providing fast prefix-based searches with results
    ordered by market cap.
    """
    
    def __init__(self):
        """Initialize an empty Trie."""
        self.root = TrieNode()

    def insert(self, ticker: str, market_cap: Union[int, float]) -> None:
        """Insert a ticker symbol with its market cap into the Trie.
        
        Args:
            ticker: The ticker symbol to insert
            market_cap: The market capitalization value
            
        Raises:
            InvalidTickerError: If ticker is invalid or market_cap is negative
        """
        if not ticker or not ticker.isalpha() or not ticker.isupper():
            raise InvalidTickerError(f"Invalid ticker symbol: {ticker}")
        if market_cap < 0:
            raise InvalidTickerError(f"Invalid market cap for {ticker}: {market_cap}")

        try:
            market_cap = int(float(market_cap))  # Handle string or float inputs
            node = self.root
            for char in ticker:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.market_cap = market_cap
            node.is_terminal = True
        except ValueError as e:
            raise InvalidTickerError(f"Invalid market cap value for {ticker}: {e}")

    def search(self, prefix: str) -> Optional[List[Tuple[str, int]]]:
        """Search for ticker symbols with the given prefix.
        
        Args:
            prefix: The prefix to search for
            
        Returns:
            List of (ticker, market_cap) tuples sorted by market cap,
            or None if no matches found
            
        Raises:
            InvalidTickerError: If prefix contains invalid characters
        """
        if not prefix:
            return None
        if not prefix.isalpha() or not prefix.isupper():
            raise InvalidTickerError(f"Invalid ticker prefix: {prefix}")

        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]

        results = self._collect_matches(node, prefix)
        return results if results else None

    def _collect_matches(self, node: TrieNode, prefix: str) -> List[Tuple[str, int]]:
        """Collect all matching tickers from the current node.
        
        Args:
            node: Current TrieNode in traversal
            prefix: Current prefix being built
            
        Returns:
            List of (ticker, market_cap) tuples for matches
        """
        exact_matches = []
        prefix_matches = []

        # Add exact match if present
        if node.is_terminal:
            exact_matches.append((prefix, node.market_cap))

        # Recursively collect matches from children
        for char, child in node.children.items():
            child_prefix = prefix + char
            child_results = self._collect_matches(child, child_prefix)
            prefix_matches.extend(child_results)

        # Sort prefix matches by market cap
        prefix_matches.sort(key=lambda x: x[1], reverse=True)

        # Combine results: exact matches first, then top prefix matches
        return exact_matches + prefix_matches[:MAX_RESULTS]

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> 'Trie':
        """Load a Trie from a pickle file.
        
        Args:
            file_path: Path to the pickle file
            
        Returns:
            Loaded Trie instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            TrieError: If file is corrupted or invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Trie file not found: {file_path}")

        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                if not isinstance(data, dict) or 'trie' not in data:
                    raise TrieError("Invalid Trie file format")
                return data['trie']
        except (pickle.UnpicklingError, EOFError) as e:
            raise TrieError(f"Error loading Trie: {e}")

    def save(self, file_path: Union[str, Path]) -> None:
        """Save the Trie to a pickle file.
        
        Args:
            file_path: Path where to save the Trie
            
        Raises:
            TrieError: If saving fails
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'wb') as f:
                pickle.dump({'trie': self}, f)
        except (pickle.PicklingError, OSError) as e:
            raise TrieError(f"Error saving Trie: {e}")

def create_trie(tickers: List[Tuple[str, Union[int, float]]]) -> Trie:
    """Create a new Trie from a list of tickers and market caps.
    
    Args:
        tickers: List of (ticker, market_cap) tuples
        
    Returns:
        Populated Trie instance
        
    Raises:
        InvalidTickerError: If any ticker data is invalid
    """
    trie = Trie()
    for ticker, market_cap in tickers:
        try:
            trie.insert(ticker, market_cap)
        except InvalidTickerError as e:
            logger.warning(f"Skipping invalid ticker: {e}")
            continue
    return trie

def main():
    """Main function to create and save the Trie."""
    try:
        logger.info("Starting Trie creation...")
        
        # Get ticker data
        tickers = extract_all_valid_tickers_and_market_caps_from_csvs()
        if not tickers:
            raise TrieError("No valid tickers found")
        
        # Create and populate Trie
        trie = create_trie(tickers)
        logger.info(f"Created Trie with {len(tickers)} tickers")
        
        # Save Trie
        trie_path = Path(os.getcwd()) / PICKLE_FILE
        trie.save(trie_path)
        logger.info(f"Saved Trie to {trie_path}")
        
    except Exception as e:
        logger.error(f"Error creating Trie: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
