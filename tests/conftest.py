import pytest
import os
import sqlite3
from pathlib import Path
import pandas as pd
from typing import Generator

# Test database paths
TEST_DB_DIR = Path("tests/test_dbs")
TEST_FINANCIAL_DB = TEST_DB_DIR / "test_financial_data.db"
TEST_DIVIDEND_DB = TEST_DB_DIR / "test_dividend_data.db"
TEST_EARNINGS_DB = TEST_DB_DIR / "test_earnings_data.db"
TEST_STOCK_INFO_DB = TEST_DB_DIR / "test_stock_info.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """Create test directories and clean up old test databases."""
    TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean up any existing test databases
    for db_path in [TEST_FINANCIAL_DB, TEST_DIVIDEND_DB, TEST_EARNINGS_DB, TEST_STOCK_INFO_DB]:
        if db_path.exists():
            db_path.unlink()

@pytest.fixture
def test_db_connection(request) -> Generator[sqlite3.Connection, None, None]:
    """Provide a database connection for testing."""
    db_path = request.param if hasattr(request, 'param') else TEST_FINANCIAL_DB
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()

@pytest.fixture
def sample_stock_data() -> dict:
    """Provide sample stock data for testing."""
    return {
        'AAPL': {
            'marketCap': 3000000000000,
            'profitMargins': 0.25,
            'revenue': 400000000000,
            'dividendYield': 0.005
        },
        'MSFT': {
            'marketCap': 2800000000000,
            'profitMargins': 0.35,
            'revenue': 200000000000,
            'dividendYield': 0.008
        }
    }

@pytest.fixture
def sample_financial_data() -> dict:
    """Provide sample financial statement data for testing."""
    return {
        'AAPL': {
            2024: {
                'Revenue': 400000000000,
                'EBITDA': 150000000000,
                'NetIncome': 100000000000,
                'FCF': 90000000000
            }
        }
    }

@pytest.fixture
def sample_dividend_data() -> dict:
    """Provide sample dividend data for testing."""
    return {
        'AAPL': [
            {'date': '2024-01', 'amount': 0.24},
            {'date': '2024-04', 'amount': 0.24}
        ]
    }
