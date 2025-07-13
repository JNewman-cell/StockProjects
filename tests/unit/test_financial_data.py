import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from StockTickers.financial_statements_db import FinancialDatabase, FinancialRatios
from yahooquery import Ticker

def test_database_creation(test_db_connection):
    """Test that the database is created with correct schema."""
    cursor = test_db_connection.cursor()
    
    # Check if tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='stocks'
    """)
    assert cursor.fetchone() is not None

    # Check table schema
    cursor.execute("PRAGMA table_info(stocks)")
    columns = {row[1] for row in cursor.fetchall()}
    
    expected_columns = {
        'id', 'ticker', 'year', 'revenue', 'ebitda', 'fcf', 'sbc',
        'net_income', 'eps', 'cash', 'debt', 'shares_outstanding'
    }
    assert expected_columns.issubset(columns)

def test_data_insertion(test_db_connection, sample_financial_data):
    """Test inserting financial data."""
    db = FinancialDatabase(test_db_connection)
    
    # Insert test data
    ticker = 'AAPL'
    year = 2024
    data = sample_financial_data[ticker][year]
    db.insert_financial_data(ticker, year, data)
    
    # Verify insertion
    cursor = test_db_connection.cursor()
    cursor.execute(
        "SELECT * FROM stocks WHERE ticker=? AND year=?",
        (ticker, year)
    )
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == ticker
    assert row[2] == year
    assert row[3] == data['Revenue']

def test_data_validation():
    """Test data validation logic."""
    with pytest.raises(ValueError):
        FinancialRatios(
            ticker='INVALID',
            year=-1,
            revenue='invalid'
        )

def test_historical_data_retrieval(test_db_connection, sample_financial_data):
    """Test retrieving historical financial data."""
    db = FinancialDatabase(test_db_connection)
    
    # Insert multiple years of data
    ticker = 'AAPL'
    current_year = datetime.now().year
    
    for year in range(current_year - 2, current_year + 1):
        data = sample_financial_data[ticker][2024].copy()  # Use 2024 data as template
        db.insert_financial_data(ticker, year, data)
    
    # Retrieve historical data
    history = db.get_historical_data(ticker)
    assert len(history) == 3
    assert all(isinstance(row['year'], int) for row in history)

def test_data_updates(test_db_connection, sample_financial_data):
    """Test updating existing financial data."""
    db = FinancialDatabase(test_db_connection)
    
    # Insert initial data
    ticker = 'AAPL'
    year = 2024
    initial_data = sample_financial_data[ticker][year]
    db.insert_financial_data(ticker, year, initial_data)
    
    # Update with new data
    updated_data = initial_data.copy()
    updated_data['Revenue'] *= 1.1  # Increase revenue by 10%
    db.insert_financial_data(ticker, year, updated_data)
    
    # Verify update
    cursor = test_db_connection.cursor()
    cursor.execute(
        "SELECT revenue FROM stocks WHERE ticker=? AND year=?",
        (ticker, year)
    )
    assert cursor.fetchone()[0] == updated_data['Revenue']

def test_data_consistency(test_db_connection, sample_financial_data):
    """Test data consistency and relationships."""
    db = FinancialDatabase(test_db_connection)
    
    ticker = 'AAPL'
    year = 2024
    data = sample_financial_data[ticker][year]
    
    # Insert data
    db.insert_financial_data(ticker, year, data)
    
    # Verify relationships
    cursor = test_db_connection.cursor()
    cursor.execute("""
        SELECT * FROM stocks 
        WHERE ticker=? AND year=?
    """, (ticker, year))
    row = dict(cursor.fetchone())
    
    # Check that net income is less than or equal to EBITDA
    assert row['net_income'] <= row['ebitda']
    
    # Check that cash is non-negative
    assert row['cash'] >= 0
