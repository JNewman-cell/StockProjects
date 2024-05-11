from flask import Flask, render_template, request, jsonify
import pickle
import sqlite3
import yfinance as yf
import datetime
import pytz
import os
from create_Trie import TrieNode, Trie

# print("Current working directory:", os.getcwd())

app = Flask(__name__)

print(os.getcwd()+'/trie.pkl')
with open(os.getcwd()+'/trie.pkl', 'rb') as f:
    data = pickle.load(f)
    trie = data['trie']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    prefix = request.args.get('prefix', '')
    results = trie.search(prefix.upper())
    return jsonify(results)

@app.route('/companyinfo', methods=['GET'])
def companyinfo():
	ticker = request.args.get('ticker')
	info = yf.Ticker(ticker)
	return jsonify(info)

@app.route('/stockprice', methods=['GET'])
def company_stock_price():
    ticker = request.args.get('ticker')
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=5*365)

    # Download stock price data
    stock_data = yf.download(ticker, start=start_date, end=end_date, interval='1wk')
    
    # Extract date and closing price
    dates = stock_data.index.strftime('%Y-%m-%d').tolist()
    prices = stock_data['Close'].tolist()
    
    return jsonify({'dates': dates, 'prices': prices})

@app.route('/dividends', methods=['GET'])
def dividends():
    ticker = request.args.get('ticker')
    # Fetch dividend data using yfinance
    div_data = yf.Ticker(ticker).dividends
    # Filter dividend data for the last 10 years
    end_date = datetime.datetime.now(pytz.utc)
    start_date = end_date - datetime.timedelta(days=365 * 10)
    start_date = start_date.replace(tzinfo=pytz.utc)  # Make start_date timezone-aware
    # Filter dividends and remove timestamps
    dividends = [{'date': date.strftime('%Y-%m-%d'), 'amount': float(amount)} for date, amount in div_data.items() if date >= start_date]
    return jsonify(dividends)

# Function to connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('financial_data.db')
    return conn

# Route to handle graph data request
@app.route('/graphs', methods=['GET'])
def graphs():
	ticker = request.args.get('ticker')
	conn = connect_db()
	cursor = conn.cursor()
	cursor.execute("SELECT year, revenue, ebitda, fcf, sbc, net_income, eps, cash, debt, shares_outstanding FROM stocks WHERE ticker = ? ORDER BY year", (ticker,))
	data = cursor.fetchall()
	# print(ticker)
	# print(data)
	conn.close()
	return jsonify(data)

if __name__ == '__main__':
    app.run()
