import sqlite3
import datetime
import json
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
from dataclasses import dataclass
from tqdm import tqdm
from yahooquery import Ticker
from tenacity import retry, stop_after_attempt, wait_exponential
from csv_manipulation import extract_all_valid_tickers_from_csvs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EarningsData:
    """Data class to represent earnings information."""
    ticker: str
    date: str
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None

class EarningsDatabase:
    """Class to manage earnings database operations."""
    
    def __init__(self, db_path: str = 'FlaskApp/earnings_data.db'):
        """Initialize the EarningsDatabase.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._create_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _create_database(self) -> None:
        """Create the earnings database if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    eps_estimate REAL,
                    eps_actual REAL,
                    revenue_estimate REAL,
                    revenue_actual REAL,
                    UNIQUE(ticker, date)
                )''')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating database: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_earnings_date_api(self, ticker: str) -> Optional[str]:
        """Get earnings date from Yahoo Finance API with retry logic.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Formatted earnings date or None if not found
        """
        try:
            ticker_obj = Ticker(ticker, timeout=30)
            calendar_info = ticker_obj.calendar_events
            
            if isinstance(calendar_info, dict) and ticker in calendar_info:
                earnings_dates = calendar_info[ticker].get('earnings', {}).get('earningsDate', [])
                if earnings_dates:
                    return earnings_dates[0].strftime('%Y-%m-%d')
            return None
            
        except Exception as e:
            logger.error(f"Error fetching earnings date for {ticker}: {e}")
            return None

    def get_earnings_date(self, ticker: str) -> Optional[EarningsData]:
        """Get earnings information from database.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            EarningsData object or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ticker, date, eps_estimate, eps_actual, 
                           revenue_estimate, revenue_actual 
                    FROM stocks 
                    WHERE ticker = ?
                """, (ticker,))
                row = cursor.fetchone()
                
                if row:
                    return EarningsData(
                        ticker=row[0],
                        date=row[1],
                        eps_estimate=row[2],
                        eps_actual=row[3],
                        revenue_estimate=row[4],
                        revenue_actual=row[5]
                    )
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error for ticker {ticker}: {e}")
            return None

    def ticker_exists(self, ticker: str) -> bool:
        """Check if a ticker exists in the database.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if ticker exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM stocks WHERE ticker = ?", (ticker,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking ticker existence for {ticker}: {e}")
            return False

    def insert_earnings(self, data: EarningsData) -> bool:
        """Insert or update earnings data.
        
        Args:
            data: EarningsData object containing the data to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO stocks 
                    (ticker, date, eps_estimate, eps_actual, revenue_estimate, revenue_actual)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data.ticker, data.date, data.eps_estimate, data.eps_actual,
                    data.revenue_estimate, data.revenue_actual
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting data for {data.ticker}: {e}")
            return False

    def delete_ticker(self, ticker: str) -> bool:
        """Delete a ticker from the database.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM stocks WHERE ticker = ?", (ticker,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting ticker {ticker}: {e}")
            return False

    def get_all_earnings(self) -> List[EarningsData]:
        """Get all earnings data from database.
        
        Returns:
            List of EarningsData objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ticker, date, eps_estimate, eps_actual, 
                           revenue_estimate, revenue_actual 
                    FROM stocks
                """)
                return [
                    EarningsData(
                        ticker=row[0],
                        date=row[1],
                        eps_estimate=row[2],
                        eps_actual=row[3],
                        revenue_estimate=row[4],
                        revenue_actual=row[5]
                    )
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            logger.error(f"Error fetching all earnings data: {e}")
            return []

    def update_earnings_cache(self) -> None:
        """Update earnings database and weekly earnings cache."""
        today = datetime.datetime.today()
        one_week_from_now = today + datetime.timedelta(days=7)
        new_weekly_earnings = []
        
        try:
            # Load existing weekly earnings
            weekly_earnings_path = Path('StockTickers/weekly_earnings.json')
            if weekly_earnings_path.exists():
                with weekly_earnings_path.open('r') as f:
                    weekly_earnings = json.load(f)
            else:
                weekly_earnings = []

            # Get all tickers
            tickers = extract_all_valid_tickers_from_csvs()
            
            for ticker in tqdm(tickers, desc="Updating earnings data"):
                if not self.ticker_exists(ticker):
                    earnings_date = self.get_earnings_date_api(ticker)
                    if earnings_date:
                        try:
                            earnings_datetime = datetime.datetime.strptime(earnings_date, '%Y-%m-%d')
                            if today <= earnings_datetime <= one_week_from_now:
                                if ticker not in weekly_earnings:
                                    new_weekly_earnings.append(ticker)
                            else:
                                self.insert_earnings(EarningsData(ticker=ticker, date=earnings_date))
                        except ValueError as e:
                            logger.error(f"Error parsing date for {ticker}: {e}")
                            continue
                    time.sleep(1)  # Rate limiting
                else:
                    current_data = self.get_earnings_date(ticker)
                    if current_data:
                        earnings_datetime = datetime.datetime.strptime(current_data.date, '%Y-%m-%d')
                        if today <= earnings_datetime <= one_week_from_now:
                            if ticker not in weekly_earnings:
                                new_weekly_earnings.append(ticker)
                                self.delete_ticker(ticker)

            # Update weekly earnings cache
            with weekly_earnings_path.open('w') as f:
                json.dump(new_weekly_earnings, f)

        except Exception as e:
            logger.error(f"Error updating earnings cache: {e}")
            raise

def main():
    """Main function for testing and manual updates."""
    try:
        db = EarningsDatabase()
        all_earnings = db.get_all_earnings()
        logger.info(f"Total earnings records: {len(all_earnings)}")
        for earning in all_earnings:
            logger.info(f"{earning.ticker}: {earning.date}")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
