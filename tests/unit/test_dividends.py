import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from StockTickers.CRUD_ex_dividend_database import DividendDatabase

def test_dividend_db_creation(test_dividend_db_connection):
    """Test that the dividend database is created with correct schema."""
    cursor = test_dividend_db_connection.cursor()
    
    # Check if tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='dividends'
    """)
    assert cursor.fetchone() is not None

    # Check table schema
    cursor.execute("PRAGMA table_info(dividends)")
    columns = {row[1] for row in cursor.fetchall()}
    
    expected_columns = {
        'id', 'ticker', 'ex_date', 'payment_date', 'amount'
    }
    assert expected_columns.issubset(columns)

def test_dividend_data_insertion(test_dividend_db_connection, sample_dividend_data):
    """Test inserting dividend data."""
    db = DividendDatabase(test_dividend_db_connection)
    
    # Insert test data
    ticker = 'AAPL'
    ex_date = datetime.now().date()
    payment_date = ex_date + timedelta(days=30)
    data = sample_dividend_data[ticker]
    db.insert_dividend(ticker, ex_date, payment_date, data['amount'])
    
    # Verify insertion
    cursor = test_dividend_db_connection.cursor()
    cursor.execute(
        "SELECT * FROM dividends WHERE ticker=? AND ex_date=?",
        (ticker, ex_date.isoformat())
    )
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == ticker
    assert row[2] == ex_date.isoformat()
    assert row[4] == data['amount']

def test_dividend_history_retrieval(test_dividend_db_connection, sample_dividend_data):
    """Test retrieving historical dividend data."""
    db = DividendDatabase(test_dividend_db_connection)
    
    # Insert multiple dividend records
    ticker = 'AAPL'
    base_date = datetime.now().date()
    
    for i in range(4):  # Last 4 quarters
        ex_date = base_date - timedelta(days=90 * i)
        payment_date = ex_date + timedelta(days=30)
        data = sample_dividend_data[ticker].copy()
        db.insert_dividend(ticker, ex_date, payment_date, data['amount'])
    
    # Retrieve dividend history
    history = db.get_dividend_history(ticker)
    assert len(history) == 4
    assert all(isinstance(row['ex_date'], str) for row in history)

def test_dividend_data_updates(test_dividend_db_connection, sample_dividend_data):
    """Test updating existing dividend data."""
    db = DividendDatabase(test_dividend_db_connection)
    
    # Insert initial data
    ticker = 'AAPL'
    ex_date = datetime.now().date()
    payment_date = ex_date + timedelta(days=30)
    initial_data = sample_dividend_data[ticker]
    db.insert_dividend(ticker, ex_date, payment_date, initial_data['amount'])
    
    # Update with new data
    updated_amount = initial_data['amount'] * 1.1  # Increase by 10%
    db.insert_dividend(ticker, ex_date, payment_date, updated_amount)
    
    # Verify update
    cursor = test_dividend_db_connection.cursor()
    cursor.execute(
        "SELECT amount FROM dividends WHERE ticker=? AND ex_date=?",
        (ticker, ex_date.isoformat())
    )
    assert cursor.fetchone()[0] == updated_amount

def test_dividend_data_validation(test_dividend_db_connection):
    """Test dividend data validation logic."""
    db = DividendDatabase(test_dividend_db_connection)
    
    ticker = 'AAPL'
    ex_date = datetime.now().date()
    payment_date = ex_date + timedelta(days=30)
    
    # Test invalid data
    with pytest.raises(ValueError):
        db.insert_dividend(ticker, ex_date, payment_date, -1.0)  # Negative dividend
        
    with pytest.raises(ValueError):
        db.insert_dividend(ticker, ex_date, ex_date - timedelta(days=1), 1.0)  # Payment date before ex-date

def test_dividend_yield_calculation(test_dividend_db_connection, sample_dividend_data):
    """Test dividend yield calculations."""
    db = DividendDatabase(test_dividend_db_connection)
    
    # Insert a year of quarterly dividends
    ticker = 'AAPL'
    base_date = datetime.now().date()
    quarterly_amount = 0.25  # $0.25 per quarter
    
    for i in range(4):
        ex_date = base_date - timedelta(days=90 * i)
        payment_date = ex_date + timedelta(days=30)
        db.insert_dividend(ticker, ex_date, payment_date, quarterly_amount)
    
    # Calculate annual dividend
    annual_dividend = db.get_annual_dividend(ticker)
    assert annual_dividend == quarterly_amount * 4  # Should be $1.00

    # Test dividend yield calculation (assuming stock price of $100)
    stock_price = 100.0
    expected_yield = (quarterly_amount * 4 / stock_price) * 100  # Should be 1%
    calculated_yield = db.calculate_dividend_yield(ticker, stock_price)
    assert calculated_yield == expected_yield
