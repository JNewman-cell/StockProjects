"""Utility functions for working with dividend data."""
import datetime
from typing import List

def get_tickers_with_dividend_within_a_week() -> List[str]:
    """Get a list of tickers that have ex-dividend dates within the next week.
    
    Returns:
        List[str]: List of ticker symbols with upcoming ex-dividend dates
    """
    today = datetime.datetime.now().date()
    end_date = today + datetime.timedelta(days=7)
    
    from CRUD_ex_dividend_database import DividendDatabase
    
    db = DividendDatabase()
    upcoming_dividends = []
    
    with db._get_connection(db.ex_dividend_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ticker FROM stocks 
            WHERE date BETWEEN ? AND ?
        """, (today.isoformat(), end_date.isoformat()))
        upcoming_dividends = [row[0] for row in cursor.fetchall()]
    
    return upcoming_dividends
