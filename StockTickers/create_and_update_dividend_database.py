import sqlite3
import datetime
import time
from pathlib import Path
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from collections import defaultdict
import pandas as pd
from yahooquery import Ticker
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dividend_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = Path('FlaskApp/dividend_data.db')
YEARS_OF_HISTORY = 15
BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY = 2

@dataclass
class DividendRecord:
    """Data class for dividend records."""
    date: str
    amount: float

class DividendDatabase:
    """Handle all database operations for dividend data."""
    
    def __init__(self, db_path: Union[str, Path] = DB_PATH):
        self.db_path = Path(db_path)
        self.ensure_db_directory()
        self.conn = None
        self.cursor = None

    def ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> None:
        """Establish database connection and create tables if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _create_tables(self) -> None:
        """Create necessary database tables."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                dividend REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (ticker, date)
            )
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_date 
            ON stocks(ticker, date)
        ''')
        self.conn.commit()

    def insert_dividend_data(self, ticker: str, records: List[DividendRecord]) -> None:
        """Insert dividend records for a ticker."""
        if not records:
            return

        rows = [(ticker, record.date, record.amount) for record in records]
        try:
            self.cursor.executemany(
                'INSERT OR REPLACE INTO stocks (ticker, date, dividend) VALUES (?, ?, ?)',
                rows
            )
            self.conn.commit()
            logger.info(f"Inserted {len(rows)} dividend records for {ticker}")
        except sqlite3.Error as e:
            logger.error(f"Database error for {ticker}: {e}")
            self.conn.rollback()

    def get_ticker_dividend_history(self, ticker: str) -> List[DividendRecord]:
        """Retrieve dividend history for a ticker."""
        try:
            self.cursor.execute(
                'SELECT date, dividend FROM stocks WHERE ticker = ? ORDER BY date DESC',
                (ticker,)
            )
            return [DividendRecord(date=row[0], amount=row[1]) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving dividend history for {ticker}: {e}")
            return []

class DividendDataFetcher:
    """Handle fetching dividend data from Yahoo Finance."""
    
    @staticmethod
    def fetch_dividend_data(ticker: str) -> List[DividendRecord]:
        """Fetch dividend history for a ticker."""
        try:
            ticker_obj = Ticker(ticker, timeout=30)
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=365 * YEARS_OF_HISTORY)
            
            div_history = ticker_obj.dividend_history(start=start_date, end=end_date)
            
            if not isinstance(div_history, pd.DataFrame) or div_history.empty:
                return []

            records = []
            for _, row in div_history.iterrows():
                if row['dividend'] > 0:
                    records.append(DividendRecord(
                        date=row['date'].strftime('%Y-%m'),
                        amount=float(row['dividend'])
                    ))
            return records

        except Exception as e:
            logger.error(f"Error fetching dividend data for {ticker}: {e}")
            return []

class DividendDataProcessor:
    """Main class for processing dividend data."""
    
    def __init__(self):
        self.db = DividendDatabase()
        self.fetcher = DividendDataFetcher()

    def process_tickers(self, tickers: List[str]) -> None:
        """Process dividend data for multiple tickers."""
        try:
            self.db.connect()
            
            for i in range(0, len(tickers), BATCH_SIZE):
                batch = tickers[i:i + BATCH_SIZE]
                self._process_batch(batch)
                
                if i + BATCH_SIZE < len(tickers):
                    logger.info(f"Sleeping between batches...")
                    time.sleep(2)  # Prevent rate limiting
                    
        finally:
            self.db.close()

    def _process_batch(self, tickers: List[str]) -> None:
        """Process a batch of tickers."""
        for ticker in tqdm(tickers, desc="Processing dividend data"):
            records = self.fetcher.fetch_dividend_data(ticker)
            if records:
                self.db.insert_dividend_data(ticker, records)
            time.sleep(0.5)  # Small delay between requests

def get_tickers_with_dividend_within_a_week() -> List[str]:
    """Get list of tickers with upcoming dividends."""
    from csv_manipulation import extract_all_valid_tickers_from_csvs
    from CRUD_ex_dividend_database import get_tickers_with_dividend_within_a_week
    return get_tickers_with_dividend_within_a_week()

def main():
    logger.info("Starting dividend data update process")
    
    try:
        tickers = get_tickers_with_dividend_within_a_week()
        logger.info(f"Found {len(tickers)} tickers to process")
        
        processor = DividendDataProcessor()
        processor.process_tickers(tickers)
        
        logger.info("Dividend data update completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
