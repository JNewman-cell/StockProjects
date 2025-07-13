import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from StockTickers.CRUD_earnings_database import EarningsDatabase

def test_earnings_db_creation(test_earnings_db_connection):
    """Test that the earnings database is created with correct schema."""
    cursor = test_earnings_db_connection.cursor()
    
    # Check if tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='earnings'
    """)
    assert cursor.fetchone() is not None

    # Check table schema
    cursor.execute("PRAGMA table_info(earnings)")
    columns = {row[1] for row in cursor.fetchall()}
    
    expected_columns = {
        'id', 'ticker', 'date', 'eps_estimate', 'eps_actual',
        'revenue_estimate', 'revenue_actual'
    }
    assert expected_columns.issubset(columns)

def test_earnings_data_insertion(test_earnings_db_connection, sample_earnings_data):
    """Test inserting earnings data."""
    db = EarningsDatabase(test_earnings_db_connection)
    
    # Insert test data
    ticker = 'AAPL'
    date = datetime.now().date()
    data = sample_earnings_data[ticker]
    db.insert_earnings(ticker, date, data)
    
    # Verify insertion
    cursor = test_earnings_db_connection.cursor()
    cursor.execute(
        "SELECT * FROM earnings WHERE ticker=? AND date=?",
        (ticker, date.isoformat())
    )
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == ticker
    assert row[2] == date.isoformat()
    assert row[3] == data['eps_estimate']

def test_earnings_history_retrieval(test_earnings_db_connection, sample_earnings_data):
    """Test retrieving historical earnings data."""
    db = EarningsDatabase(test_earnings_db_connection)
    
    # Insert multiple earnings records
    ticker = 'AAPL'
    base_date = datetime.now().date()
    
    for i in range(4):  # Last 4 quarters
        date = base_date - timedelta(days=90 * i)
        data = sample_earnings_data[ticker].copy()
        db.insert_earnings(ticker, date, data)
    
    # Retrieve earnings history
    history = db.get_earnings_history(ticker)
    assert len(history) == 4
    assert all(isinstance(row['date'], str) for row in history)

def test_earnings_data_updates(test_earnings_db_connection, sample_earnings_data):
    """Test updating existing earnings data."""
    db = EarningsDatabase(test_earnings_db_connection)
    
    # Insert initial data
    ticker = 'AAPL'
    date = datetime.now().date()
    initial_data = sample_earnings_data[ticker]
    db.insert_earnings(ticker, date, initial_data)
    
    # Update with new data
    updated_data = initial_data.copy()
    updated_data['eps_actual'] = initial_data['eps_estimate'] * 1.1  # Beat estimates by 10%
    db.insert_earnings(ticker, date, updated_data)
    
    # Verify update
    cursor = test_earnings_db_connection.cursor()
    cursor.execute(
        "SELECT eps_actual FROM earnings WHERE ticker=? AND date=?",
        (ticker, date.isoformat())
    )
    assert cursor.fetchone()[0] == updated_data['eps_actual']

def test_earnings_data_validation(test_earnings_db_connection):
    """Test earnings data validation logic."""
    db = EarningsDatabase(test_earnings_db_connection)
    
    ticker = 'AAPL'
    date = datetime.now().date()
    
    # Test invalid data
    with pytest.raises(ValueError):
        db.insert_earnings(ticker, date, {
            'eps_estimate': 'invalid',
            'eps_actual': 1.0,
            'revenue_estimate': 1000000,
            'revenue_actual': 1100000
        })
        
    with pytest.raises(ValueError):
        db.insert_earnings(ticker, date, {
            'eps_estimate': -100,  # Unrealistic value
            'eps_actual': 1.0,
            'revenue_estimate': 1000000,
            'revenue_actual': 1100000
        })
