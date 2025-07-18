import sqlite3
import datetime
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from yahooquery import Ticker
from tenacity import retry, stop_after_attempt, wait_exponential
from csv_manipulation import extract_all_valid_tickers_from_csvs
from .dividend_utils import get_tickers_with_dividend_within_a_week

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DividendData:
    """Data class to represent dividend information."""
    ticker: str
    ex_date: str
    payment_date: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None  # 'monthly', 'quarterly', 'semi-annual', 'annual'
    yield_value: Optional[float] = None
    last_updated: Optional[str] = None

class DividendDatabase:
    """Class to manage dividend database operations."""
    
    def __init__(
        self, 
        ex_dividend_db_path: str = 'FlaskApp/ex_dividend_data.db',
        dividend_history_db_path: str = 'FlaskApp/dividend_data.db'
    ):
        """Initialize the DividendDatabase.
        
        Args:
            ex_dividend_db_path: Path to the ex-dividend dates database
            dividend_history_db_path: Path to the dividend history database
        """
        self.ex_dividend_db_path = ex_dividend_db_path
        self.dividend_history_db_path = dividend_history_db_path
        self._create_databases()

    @contextmanager
    def _get_connection(self, db_path: str):
        """Context manager for database connections.
        
        Args:
            db_path: Path to the database to connect to
        """
        conn = sqlite3.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _create_databases(self) -> None:
        """Create the dividend databases if they don't exist."""
        try:
            # Create ex-dividend database
            with self._get_connection(self.ex_dividend_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    payment_date TEXT,
                    amount REAL,
                    frequency TEXT,
                    yield REAL,
                    last_updated TEXT,
                    UNIQUE(ticker, date)
                )''')
                conn.commit()

            # Create dividend history database
            with self._get_connection(self.dividend_history_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    UNIQUE(ticker, date)
                )''')
                conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Error creating databases: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_dividend_info_api(self, ticker: str) -> Optional[DividendData]:
        """Get dividend information from Yahoo Finance API with retry logic.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DividendData object or None if not found
        """
        try:
            ticker_obj = Ticker(ticker, timeout=30)
            calendar_info = ticker_obj.calendar_events
            
            if isinstance(calendar_info, dict) and ticker in calendar_info:
                ex_div_date = calendar_info[ticker].get('exDividendDate')
                if ex_div_date:
                    # Get additional dividend information
                    summary_detail = ticker_obj.summary_detail
                    if isinstance(summary_detail, dict) and ticker in summary_detail:
                        details = summary_detail[ticker]
                        return DividendData(
                            ticker=ticker,
                            ex_date=ex_div_date.strftime('%Y-%m-%d'),
                            amount=details.get('dividendRate'),
                            yield_value=details.get('dividendYield'),
                            frequency=self._determine_dividend_frequency(details.get('dividendRate'), 
                                                                      details.get('trailingAnnualDividendRate')),
                            last_updated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
            return None
            
        except Exception as e:
            logger.error(f"Error fetching dividend info for {ticker}: {e}")
            return None

    def _determine_dividend_frequency(self, div_rate: Optional[float], annual_rate: Optional[float]) -> Optional[str]:
        """Determine dividend payment frequency based on rates.
        
        Args:
            div_rate: Single dividend payment amount
            annual_rate: Annual dividend total
            
        Returns:
            String indicating payment frequency
        """
        if not div_rate or not annual_rate:
            return None
            
        payments_per_year = round(annual_rate / div_rate)
        frequency_map = {
            1: 'annual',
            2: 'semi-annual',
            4: 'quarterly',
            12: 'monthly'
        }
        return frequency_map.get(payments_per_year)

    def get_ex_dividend_date(self, ticker: str) -> Optional[DividendData]:
        """Get dividend information from database.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DividendData object or None if not found
        """
        try:
            with self._get_connection(self.ex_dividend_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ticker, date, payment_date, amount, frequency, yield, last_updated
                    FROM stocks 
                    WHERE ticker = ?
                """, (ticker,))
                row = cursor.fetchone()
                
                if row:
                    return DividendData(
                        ticker=row[0],
                        ex_date=row[1],
                        payment_date=row[2],
                        amount=row[3],
                        frequency=row[4],
                        yield_value=row[5],
                        last_updated=row[6]
                    )
                return None
        except sqlite3.Error as e:
            logger.error(f"Database error for ticker {ticker}: {e}")
            return None

    def get_dividend_history(self, ticker: str, months: int = 12) -> List[Dict[str, Any]]:
        """Get dividend payment history for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            months: Number of months of history to retrieve
            
        Returns:
            List of dividend payments with dates and amounts
        """
        try:
            with self._get_connection(self.dividend_history_db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.datetime.now() - relativedelta(months=months)).strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT date, amount 
                    FROM stocks 
                    WHERE ticker = ? AND date >= ?
                    ORDER BY date DESC
                """, (ticker, cutoff_date))
                return [{"date": row[0], "amount": row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching dividend history for {ticker}: {e}")
            return []

    def calculate_annual_yield(self, ticker: str, current_price: float) -> Optional[float]:
        """Calculate annual dividend yield based on recent payments.
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current stock price
            
        Returns:
            Annual dividend yield as a percentage
        """
        try:
            history = self.get_dividend_history(ticker)
            if not history:
                return None
                
            # Calculate annual rate based on payment frequency
            annual_amount = self._calculate_annual_amount(history)
            if annual_amount and current_price > 0:
                return (annual_amount / current_price) * 100
            return None
        except Exception as e:
            logger.error(f"Error calculating yield for {ticker}: {e}")
            return None

    def _calculate_annual_amount(self, history: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate annual dividend amount based on payment history.
        
        Args:
            history: List of dividend payments with dates and amounts
            
        Returns:
            Estimated annual dividend amount
        """
        if not history:
            return None
            
        # Sort by date
        sorted_history = sorted(history, key=lambda x: x['date'])
        
        # Calculate payment frequency and annual amount
        if len(sorted_history) >= 2:
            first_date = datetime.datetime.strptime(sorted_history[0]['date'], '%Y-%m-%d')
            last_date = datetime.datetime.strptime(sorted_history[-1]['date'], '%Y-%m-%d')
            days_between = (last_date - first_date).days
            if days_between <= 0:
                return None
                
            payments_per_year = (365 / days_between) * (len(sorted_history) - 1)
            avg_payment = sum(payment['amount'] for payment in sorted_history) / len(sorted_history)
            return avg_payment * round(payments_per_year)
            
        return sorted_history[0]['amount'] * 4  # Assume quarterly if only one payment

    def update_ex_dividend_cache(self) -> None:
        """Update ex-dividend database and weekly dividend cache."""
        today = datetime.datetime.today()
        one_week_from_now = today + datetime.timedelta(days=7)
        new_weekly_dividends = []
        
        try:
            # Load existing weekly dividends
            weekly_dividends_path = Path('StockTickers/weekly_dividends.json')
            if weekly_dividends_path.exists():
                with weekly_dividends_path.open('r') as f:
                    weekly_dividends = json.load(f)
            else:
                weekly_dividends = []

            # Get all tickers
            tickers = extract_all_valid_tickers_from_csvs()
            
            for ticker in tqdm(tickers, desc="Updating dividend data"):
                latest_div = self.get_dividend_history(ticker, months=7)
                
                if latest_div:  # Only check tickers with dividend history
                    if not self.get_ex_dividend_date(ticker):
                        div_info = self.get_dividend_info_api(ticker)
                        if div_info:
                            try:
                                ex_date = datetime.datetime.strptime(div_info.ex_date, '%Y-%m-%d')
                                if today <= ex_date <= one_week_from_now:
                                    if ticker not in weekly_dividends:
                                        new_weekly_dividends.append(ticker)
                                else:
                                    self.insert_dividend(div_info)
                            except ValueError as e:
                                logger.error(f"Error parsing date for {ticker}: {e}")
                                continue
                        time.sleep(1)  # Rate limiting
                    else:
                        current_data = self.get_ex_dividend_date(ticker)
                        if current_data:
                            ex_date = datetime.datetime.strptime(current_data.ex_date, '%Y-%m-%d')
                            if today <= ex_date <= one_week_from_now:
                                if ticker not in weekly_dividends:
                                    new_weekly_dividends.append(ticker)
                                    self.delete_dividend(ticker)

            # Update weekly dividends cache
            with weekly_dividends_path.open('w') as f:
                json.dump(new_weekly_dividends, f)

        except Exception as e:
            logger.error(f"Error updating dividend cache: {e}")
            raise

    def insert_dividend(self, data: DividendData) -> bool:
        """Insert or update dividend data.
        
        Args:
            data: DividendData object containing the data to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection(self.ex_dividend_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO stocks 
                    (ticker, date, payment_date, amount, frequency, yield, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.ticker, data.ex_date, data.payment_date, data.amount,
                    data.frequency, data.yield_value, data.last_updated
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting data for {data.ticker}: {e}")
            return False

    def delete_dividend(self, ticker: str) -> bool:
        """Delete a dividend record from the database.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection(self.ex_dividend_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM stocks WHERE ticker = ?", (ticker,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting dividend for {ticker}: {e}")
            return False

def main():
    """Main function for testing and manual updates."""
    try:
        db = DividendDatabase()
        # Example usage
        ticker = 'AAPL'
        div_info = db.get_dividend_info_api(ticker)
        if div_info:
            logger.info(f"Dividend info for {ticker}:")
            logger.info(f"Ex-Date: {div_info.ex_date}")
            logger.info(f"Amount: {div_info.amount}")
            logger.info(f"Frequency: {div_info.frequency}")
            
            # Calculate yield
            current_price = 100.0  # This should be fetched from a price source
            annual_yield = db.calculate_annual_yield(ticker, current_price)
            if annual_yield:
                logger.info(f"Calculated Yield: {annual_yield:.2f}%")
    
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
