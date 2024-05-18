import sqlite3
import yfinance as yf
import csv
import time

tickers = []

def extract_tickers_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            frequency = row['Market Cap']
            if frequency != 'N/A':
                tickers.append(row['Ticker'])
    return tickers

def check_ratios(ticker, info, field):
    try:
        value = info[field]
    except Exception as e:
        print("An error occurred for ticker: {}, field: {}".format(ticker, field))
        value = None
    return value

def extract_stock_info(ticker):
    data = {}
    stock = yf.Ticker(ticker)

    ratios = stock.info
    print(ticker)
    
    # Extract data including the company name
    data = {
        'name': ratios.get('longName', 'N/A'),
        'profitMargins': check_ratios(ticker, ratios, 'profitMargins'),
        'payoutRatio': check_ratios(ticker, ratios, 'payoutRatio'),
        'dividendYield': check_ratios(ticker, ratios, 'dividendYield'),
        'twoHundredDayAverage': check_ratios(ticker, ratios, 'twoHundredDayAverage'),
        'fiftyDayAverage': check_ratios(ticker, ratios, 'fiftyDayAverage'),
        'totalCash': check_ratios(ticker, ratios, 'totalCash'),
        'totalDebt': check_ratios(ticker, ratios, 'totalDebt'),
        'earningsGrowth': check_ratios(ticker, ratios, 'earningsGrowth'),
        'revenueGrowth': check_ratios(ticker, ratios, 'revenueGrowth'),
        'trailingPE': check_ratios(ticker, ratios, 'trailingPE'),
        'forwardPE': check_ratios(ticker, ratios, 'forwardPE'),
        'trailingEps': check_ratios(ticker, ratios, 'trailingEps'),
        'forwardEps': check_ratios(ticker, ratios, 'forwardEps'),
        'ebitda': check_ratios(ticker, ratios, 'ebitda'),
        'freeCashflow': check_ratios(ticker, ratios, 'freeCashflow'),
        'marketCap': check_ratios(ticker, ratios, 'marketCap')
    }
    
    return data

def create_database():
    conn = sqlite3.connect('FlaskApp/stock_info.db')
    cursor = conn.cursor()

    # Create tables with the new structure including the company name, freeCashflow, and marketCap
    cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        ticker TEXT NOT NULL,
                        profitMargins REAL,
                        payoutRatio REAL,
                        dividendYield REAL,
                        twoHundredDayAverage REAL,
                        fiftyDayAverage REAL,
                        totalCash REAL,
                        totalDebt REAL,
                        earningsGrowth REAL,
                        revenueGrowth REAL,
                        trailingPE REAL,
                        forwardPE REAL,
                        trailingEps REAL,
                        forwardEps REAL,
                        ebitda REAL,
                        freeCashflow REAL,
                        marketCap REAL,
                        UNIQUE (ticker)
                    )''')

    conn.commit()
    return conn

def insert_data_into_database(conn, ticker, data):
    cursor = conn.cursor()

    # Prepare the data for insertion or update including the company name, freeCashflow, and marketCap
    values = (data['name'], ticker, data['profitMargins'], data['payoutRatio'], data['dividendYield'],
              data['twoHundredDayAverage'], data['fiftyDayAverage'], data['totalCash'],
              data['totalDebt'], data['earningsGrowth'], data['revenueGrowth'],
              data['trailingPE'], data['forwardPE'], data['trailingEps'], data['forwardEps'],
              data['ebitda'], data['freeCashflow'], data['marketCap'])

    # Insert or update the data including the company name, freeCashflow, and marketCap
    cursor.execute('''INSERT INTO stocks (name, ticker, profitMargins, payoutRatio, dividendYield,
                                          twoHundredDayAverage, fiftyDayAverage, totalCash, totalDebt,
                                          earningsGrowth, revenueGrowth, trailingPE, forwardPE,
                                          trailingEps, forwardEps, ebitda, freeCashflow, marketCap)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      ON CONFLICT(ticker) DO UPDATE SET
                      name=excluded.name,
                      profitMargins=excluded.profitMargins,
                      payoutRatio=excluded.payoutRatio,
                      dividendYield=excluded.dividendYield,
                      twoHundredDayAverage=excluded.twoHundredDayAverage,
                      fiftyDayAverage=excluded.fiftyDayAverage,
                      totalCash=excluded.totalCash,
                      totalDebt=excluded.totalDebt,
                      earningsGrowth=excluded.earningsGrowth,
                      revenueGrowth=excluded.revenueGrowth,
                      trailingPE=excluded.trailingPE,
                      forwardPE=excluded.forwardPE,
                      trailingEps=excluded.trailingEps,
                      forwardEps=excluded.forwardEps,
                      ebitda=excluded.ebitda,
                      freeCashflow=excluded.freeCashflow,
                      marketCap=excluded.marketCap''', values)

    conn.commit()

def printDB():
    try:
        conn = sqlite3.connect('FlaskApp/stock_info.db')
        c = conn.cursor()
        c.execute('SELECT * FROM stocks')
        rows = c.fetchall()

        if not rows:
            print("No data found in the 'stocks' table.")
        else:
            for row in rows:
                print(row)

    except sqlite3.Error as e:
        print(f"Error reading data from database: {e}")
    finally:
        if conn:
            conn.close()

def main():
    conn = create_database()

    csv_file_path = 'StockTickers/nasdaq_tickers_cleaned.csv'
    csv_file_path2 = 'StockTickers/nyse_tickers_cleaned.csv'
    extract_tickers_from_csv(csv_file_path)
    extract_tickers_from_csv(csv_file_path2)

    for ticker in tickers:
        data = extract_stock_info(ticker)
        insert_data_into_database(conn, ticker, data)
        time.sleep(1)
    conn.close()

    # Uncomment the following line if you want to print the database contents
    # printDB()

if __name__ == "__main__":
    main()
