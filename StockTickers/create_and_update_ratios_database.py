import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
from datetime import datetime
import pandas as pd
from yahooquery import Ticker
from tqdm import tqdm
from csv_manipulation import extract_all_valid_tickers_from_csvs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_ratios.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = Path('FlaskApp/stock_info.db')
BATCH_SIZE = 50
TIMEOUT = 30
RETRY_DELAY = 1

@dataclass
class FinancialRatios:
    """Data class for financial ratios."""
    name: str
    profitMargins: Optional[float] = None
    payoutRatio: Optional[float] = None
    dividendYield: Optional[float] = None
    twoHundredDayAverage: Optional[float] = None
    fiftyDayAverage: Optional[float] = None
    totalCash: Optional[float] = None
    totalDebt: Optional[float] = None
    earningsGrowth: Optional[float] = None
    revenueGrowth: Optional[float] = None
    trailingPE: Optional[float] = None
    forwardPE: Optional[float] = None
    trailingEps: Optional[float] = None
    forwardEps: Optional[float] = None
    ebitda: Optional[float] = None
    freeCashflow: Optional[float] = None
    marketCap: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialRatios':
        """Create FinancialRatios from a dictionary."""
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__})

    def to_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return tuple(getattr(self, field) for field in self.__dataclass_fields__)

class FinancialDatabase:
    """Handle all database operations for financial ratios."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.ensure_db_directory()
        self.conn = None
        self.cursor = None

    def ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> None:
        """Establish database connection and create tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self._create_tables()
            self._create_indices()
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def close(self) -> None:
        """Close database connection safely."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _create_tables(self) -> None:
        """Create necessary database tables."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    ticker TEXT NOT NULL,
                    profitMargins REAL,
                    payoutRatio REAL,
                    dividendYield REAL,
                    twoHundredDayAverage REAL,
                    fiftyDayAverage REAL,
                    totalCash REAL,
                    totalDebt REAL,
                    earningsGrowth REAL,
                    revenueGrowth REAL,
                    trailingPE REAL,
                    forwardPE REAL,
                    trailingEps REAL,
                    forwardEps REAL,
                    ebitda REAL,
                    freeCashflow REAL,
                    marketCap REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (ticker)
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def _create_indices(self) -> None:
        """Create necessary indices for better query performance."""
        try:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON stocks(ticker)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_cap ON stocks(marketCap)')
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating indices: {e}")
            raise

    def upsert_financial_ratios(self, ticker: str, ratios: FinancialRatios) -> None:
        """Insert or update financial ratios for a ticker."""
        try:
            values = (ticker,) + ratios.to_tuple()
            fields = list(FinancialRatios.__dataclass_fields__.keys())
            
            query = f'''
                INSERT INTO stocks (ticker, {', '.join(fields)})
                VALUES ({', '.join(['?'] * (len(fields) + 1))})
                ON CONFLICT(ticker) DO UPDATE SET
                {', '.join(f'{field}=excluded.{field}' for field in fields)},
                updated_at=CURRENT_TIMESTAMP
            '''
            
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug(f"Successfully updated ratios for {ticker}")
        except sqlite3.Error as e:
            logger.error(f"Database error for {ticker}: {e}")
            self.conn.rollback()

class FinancialDataFetcher:
    """Handle fetching financial data from Yahoo Finance."""

    @staticmethod
    def fetch_financial_ratios(ticker: str) -> Optional[FinancialRatios]:
        """Fetch financial ratios for a ticker."""
        try:
            stock = Ticker(ticker, timeout=TIMEOUT)
            
            # Fetch all required data in parallel
            data = {
                'quotes': stock.quotes.get(ticker, {}),
                'summary': stock.summary_detail.get(ticker, {}),
                'stats': stock.key_stats.get(ticker, {}),
                'financials': stock.financial_data.get(ticker, {})
            }
            
            # Merge all data sources
            merged_data = {}
            for source in data.values():
                if isinstance(source, dict):
                    merged_data.update(source)
            
            if not merged_data:
                logger.warning(f"No data found for {ticker}")
                return None
                
            return FinancialRatios.from_dict(merged_data)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

class FinancialDataProcessor:
    """Main class for processing financial ratios data."""
    
    def __init__(self):
        self.db = FinancialDatabase()
        self.fetcher = FinancialDataFetcher()

    def process_tickers(self, tickers: List[str]) -> None:
        """Process financial ratios for multiple tickers."""
        try:
            self.db.connect()
            
            for i in range(0, len(tickers), BATCH_SIZE):
                batch = tickers[i:i + BATCH_SIZE]
                self._process_batch(batch)
                
                if i + BATCH_SIZE < len(tickers):
                    logger.info(f"Sleeping between batches...")
                    time.sleep(RETRY_DELAY)
                    
        finally:
            self.db.close()

    def _process_batch(self, tickers: List[str]) -> None:
        """Process a batch of tickers."""
        for ticker in tqdm(tickers, desc="Processing financial ratios"):
            ratios = self.fetcher.fetch_financial_ratios(ticker)
            if ratios:
                self.db.upsert_financial_ratios(ticker, ratios)
            time.sleep(0.5)  # Small delay between requests

def main():
    logger.info("Starting financial ratios update process")
    
    try:
        tickers = extract_all_valid_tickers_from_csvs()
        logger.info(f"Found {len(tickers)} tickers to process")
        
        processor = FinancialDataProcessor()
        processor.process_tickers(tickers)
        
        logger.info("Financial ratios update completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
