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

# print(os.getcwd()+'/trie.pkl')
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

def format_percentage(value):
	if value == None:
		return 'N/A'
	# Assumes the input value is a decimal (e.g., 0.10 for 10%)
	return f"{value * 100:.2f}%"

def format_price(value):
	if value == None:
		return 'N/A'
	# Assumes the input value is a decimal (e.g., 0.10 for 10%)
	return f"{value:.2f}"

def format_value(value):
	if value == None:
		return 'N/A'
	if (value >= 1e9) or (value <= -1e9):
		# Format the value in billions
		return f"{value / 1e9:.1f}b"
	elif (value >= 1e6) or (value <= -1e6):
		# Format the value in millions
		return f"{value / 1e6:.1f}m"
	elif (value >= 1e3) or (value <= -1e3):
		# Format the value in thousands
		return f"{value / 1e3:.1f}k"
	else:
		# Return the value as is
		return f"{value}"

def format_price(value):
    # Assumes the input value is a decimal (e.g., 0.10 for 10%)
    return f"{value:.2f}"

@app.route('/companyinfo', methods=['GET'])
def companyinfo():
    ticker = request.args.get('ticker')
    conn = sqlite3.connect('stock_info.db')
    cursor = conn.cursor()
    cursor.execute("SELECT profitMargins, payoutRatio, dividendYield, twoHundredDayAverage, fiftyDayAverage, totalCash, totalDebt, earningsGrowth, revenueGrowth, trailingPE, forwardPE, trailingEps, forwardEps, ebitda FROM stocks WHERE ticker = ?", (ticker,))
    data = cursor.fetchall()
    columns = ['Profit Margin', 'Payout Ratio', 'Dividend Yield',
               '200 Day Moving Average', '50 Day Moving Average', 'Total Cash', 'Total Debt',
               'Earnings Growth', 'Revenue Growth', 'Trailing PE', 'Forward PE',
               'Trailing EPS', 'Forward EPS', 'EBITDA']
    formatted_data = []

    for row in data:
        formatted_row = list(row)
        # Formatting percentages
        formatted_row[0] = format_percentage(row[0])  # Profit Margin
        formatted_row[1] = format_percentage(row[1])  # Payout Ratio
        formatted_row[2] = format_percentage(row[2])  # Dividend Yield
        formatted_row[7] = format_percentage(row[7])  # Earnings Growth
        formatted_row[8] = format_percentage(row[8])  # Revenue Growth
        # Formatting prices
        formatted_row[3] = format_price(row[3])  # 200 Day Moving Average
        formatted_row[4] = format_price(row[4])  # 50 Day Moving Average
        formatted_row[9] = format_price(row[9])  # Trailing PE
        formatted_row[10] = format_price(row[10]) # Forward PE
        # Formatting values
        formatted_row[5] = format_value(row[5])  # Total Cash
        formatted_row[6] = format_value(row[6])  # Total Debt
        formatted_row[13] = format_value(row[13])  # EBITDA

        formatted_data.append(dict(zip(columns, formatted_row)))

    conn.close()
    print(formatted_data)

    return jsonify(formatted_data)



@app.route('/stockprice', methods=['GET'])
def company_stock_price():
    ticker = request.args.get('ticker')
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=5*365)

    # Download stock price data
    stock_data = yf.download(ticker, start=start_date, end=end_date, interval='1wk')
    
    # Extract date and closing price
    dates = stock_data.index.strftime('%Y-%m').tolist()
    prices = stock_data['Close'].tolist()
    
    return jsonify({'dates': dates, 'prices': prices})

@app.route('/dividends', methods=['GET'])
def dividends():
    ticker = request.args.get('ticker')
    conn = connect_dividend_db()
    cursor = conn.cursor()
    cursor.execute("SELECT date, dividend FROM stocks WHERE ticker = ? ORDER BY date", (ticker,))
    data = cursor.fetchall()
    # print(ticker)
    # print(data)
    conn.close()
    return jsonify(data)

# Function to connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('financial_data.db')
    return conn

# Function to connect to the dividend SQLite database
def connect_dividend_db():
    conn = sqlite3.connect('dividend_data.db')
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
