"""
Flask application for stock information and analysis.

This module provides a web interface for accessing stock data, including:
- Stock symbol search with Trie-based autocomplete
- Company financial information
- Stock price history
- Dividend history
- Financial graphs and metrics
"""

import os
import logging
import pickle
import sqlite3
import datetime
import pytz
from pathlib import Path
from datetime import timedelta
from typing import Dict, List, Optional, Union, Any
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass
from flask import Flask, render_template, request, jsonify, current_app, send_from_directory
from yahooquery import Ticker
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flask_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    """Application configuration."""
    DEBUG = False
    TESTING = False
    DATABASE_DIR = Path('FlaskApp')
    STOCK_INFO_DB = DATABASE_DIR / 'stock_info.db'
    FINANCIAL_DATA_DB = DATABASE_DIR / 'financial_data.db'
    DIVIDEND_DATA_DB = DATABASE_DIR / 'dividend_data.db'
    TRIE_FILE = DATABASE_DIR / 'trie.pkl'
    CHART_DAYS = 5 * 365  # 5 years of data
    MAX_SEARCH_RESULTS = 10
    
    # Yahoo API configuration
    YAHOO_TIMEOUT = 30
    YAHOO_MAX_RETRIES = 3
    YAHOO_RETRY_DELAY = 4
    YAHOO_MAX_RETRY_DELAY = 10

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    pass

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_DIR = Path('tests/data')

@dataclass
class CompanyInfo:
    """Data class for company information."""
    name: str
    profit_margin: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    ma_200: Optional[float] = None
    ma_50: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    earnings_growth: Optional[float] = None
    revenue_growth: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    trailing_eps: Optional[float] = None
    forward_eps: Optional[float] = None
    ebitda: Optional[float] = None
    free_cash_flow: Optional[float] = None
    market_cap: Optional[float] = None

def create_app(config_class=DevelopmentConfig) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__, static_folder='frontend/build')
    app.config.from_object(config_class)

    # Initialize Trie
    try:
        with open(app.config['TRIE_FILE'], 'rb') as f:
            app.trie = pickle.load(f)['trie']
    except Exception as e:
        logger.error(f"Failed to load Trie: {e}")
        raise

    return app

app = create_app()

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# Database utilities
@contextmanager
def get_db(db_path: Path):
    """Context manager for database connections.
    
    Args:
        db_path: Path to the database file
        
    Yields:
        sqlite3.Connection object
    """
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def handle_errors(f):
    """Decorator to handle errors in route handlers."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    return decorated_function

# Formatting utilities
def format_percentage(value: Optional[float]) -> str:
    """Format a decimal value as a percentage string."""
    if value is None:
        return 'N/A'
    return f"{value * 100:.2f}%"

def format_decimal(value: Optional[float]) -> str:
    """Format a decimal value with 2 decimal places."""
    if value is None:
        return 'N/A'
    return f"{value:.2f}"

def format_currency(value: Optional[float]) -> str:
    """Format a value as currency with appropriate scale (K, M, B, T)."""
    if value is None:
        return 'N/A'
    
    scales = [
        (1e12, 't'),
        (1e9, 'b'),
        (1e6, 'm'),
        (1e3, 'k')
    ]
    
    for scale, suffix in scales:
        if abs(value) >= scale:
            return f"{value / scale:.1f}{suffix}"
    
    return f"{value}"

# API routes
@app.route('/api/suggestions/<query>')
def get_suggestions(query):
    # Your existing suggestion logic here
    pass

@app.route('/api/stock/<symbol>')
def get_stock_info(symbol):
    # Your existing stock info logic here
    pass

# Routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/search')
@handle_errors
def search():
    """Handle stock symbol search requests."""
    prefix = request.args.get('prefix', '').upper()
    if not prefix:
        return jsonify([])
        
    results = app.trie.search(prefix)
    return jsonify(results)

@app.route('/companyinfo')
@handle_errors
def company_info():
    """Get company information for a ticker symbol."""
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker symbol required'}), 400

    with get_db(app.config['STOCK_INFO_DB']) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT profitMargins, payoutRatio, dividendYield, 
                   twoHundredDayAverage, fiftyDayAverage, totalCash, 
                   totalDebt, earningsGrowth, revenueGrowth, 
                   trailingPE, forwardPE, trailingEps, forwardEps, 
                   ebitda, freeCashflow, marketCap, name 
            FROM stocks 
            WHERE ticker = ?
        """, (ticker,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Company not found'}), 404

        info = CompanyInfo(
            profit_margin=row[0],
            payout_ratio=row[1],
            dividend_yield=row[2],
            ma_200=row[3],
            ma_50=row[4],
            total_cash=row[5],
            total_debt=row[6],
            earnings_growth=row[7],
            revenue_growth=row[8],
            trailing_pe=row[9],
            forward_pe=row[10],
            trailing_eps=row[11],
            forward_eps=row[12],
            ebitda=row[13],
            free_cash_flow=row[14],
            market_cap=row[15],
            name=row[16]
        )

        return jsonify({
            'Profit Margin': format_percentage(info.profit_margin),
            'Payout Ratio': format_percentage(info.payout_ratio),
            'Dividend Yield': format_percentage(info.dividend_yield),
            '200 Day MA': f"${format_decimal(info.ma_200)}",
            '50 Day MA': f"${format_decimal(info.ma_50)}",
            'Total Cash': format_currency(info.total_cash),
            'Total Debt': format_currency(info.total_debt),
            'Earnings Growth': format_percentage(info.earnings_growth),
            'Revenue Growth': format_percentage(info.revenue_growth),
            'Trailing PE': format_decimal(info.trailing_pe),
            'Forward PE': format_decimal(info.forward_pe),
            'Trailing EPS': format_decimal(info.trailing_eps),
            'Forward EPS': format_decimal(info.forward_eps),
            'EBITDA': format_currency(info.ebitda),
            'Free Cash Flow': format_currency(info.free_cash_flow),
            'Market Cap': format_currency(info.market_cap),
            'Name': info.name
        })

@app.route('/stockprice')
@handle_errors
def stock_price():
    """Get historical stock price data with retry logic."""
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker symbol required'}), 400

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda _: None
    )
    def fetch_stock_data(symbol: str) -> Optional[Dict]:
        """Fetch stock data with retry logic."""
        ticker_obj = Ticker(symbol, timeout=30)
        end_date = datetime.datetime.now()
        start_date = end_date - timedelta(days=app.config['CHART_DAYS'])

        history = ticker_obj.history(
            period='5y',
            interval='1wk',
            start=start_date,
            end=end_date
        )

        if isinstance(history, Dict):
            logger.error(f"Error in Yahoo API response for {symbol}")
            return None

        # Reset index to handle multi-level index
        history = history.reset_index()
        return {
            'dates': history['date'].dt.strftime('%Y-%m').tolist(),
            'prices': history['close'].tolist(),
            'volume': history['volume'].tolist(),
            'high': history['high'].tolist(),
            'low': history['low'].tolist(),
            'open': history['open'].tolist()
        }

    try:
        data = fetch_stock_data(ticker)
        if data is None:
            return jsonify({'error': 'Failed to fetch stock data'}), 500
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {e}")
        return jsonify({'error': 'Failed to fetch stock data'}), 500

@app.route('/dividends')
@handle_errors
def dividends():
    """Get dividend history for a ticker."""
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker symbol required'}), 400

    with get_db(app.config['DIVIDEND_DATA_DB']) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date, dividend FROM stocks WHERE ticker = ? ORDER BY date",
            (ticker,)
        )
        return jsonify(cursor.fetchall())

@app.route('/graphs')
@handle_errors
def graphs():
    """Get financial data for graphs."""
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'Ticker symbol required'}), 400

    with get_db(app.config['FINANCIAL_DATA_DB']) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT year, revenue, ebitda, fcf, sbc, net_income, 
                   eps, cash, debt, shares_outstanding 
            FROM stocks 
            WHERE ticker = ? 
            ORDER BY year
        """, (ticker,))
        return jsonify(cursor.fetchall())

if __name__ == '__main__':
    app.run()
