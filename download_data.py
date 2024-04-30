import yfinance as yf

msft = yf.Ticker("MSFT")

# get all stock info
print(msft.info)

financial_data = [
    'totalRevenue',
    'freeCashflow',
    'operatingCashflow',
    'ebitda',
    'totalCash',
    'totalDebt',
    'quickRatio',
    'currentRatio',
    'debtToEquity',
    'returnOnAssets',
    'returnOnEquity',
    'earningsGrowth',
    'revenueGrowth',
    'grossMargins',
    'ebitdaMargins',
    'operatingMargins'
]

# Print out the financial data
for f in financial_data:
    print(f+': '+str(msft.info[f]))


# # get historical market data
hist = msft.history(period="max")

# # show meta information about the history (requires history() to be called first)
print(msft.history_metadata)

# # show actions (dividends, splits, capital gains)
# msft.actions
# msft.dividends
# msft.splits
# msft.capital_gains  # only for mutual funds & etfs

# # show share count
# msft.get_shares_full(start="2022-01-01", end=None)

# # show financials:
# # - income statement
# msft.income_stmt
# msft.quarterly_income_stmt
# # - balance sheet
# msft.balance_sheet
# msft.quarterly_balance_sheet
# # - cash flow statement
# msft.cashflow
# msft.quarterly_cashflow
# # see `Ticker.get_income_stmt()` for more options

# # show holders
# msft.major_holders
# msft.institutional_holders
# msft.mutualfund_holders
print(msft.insider_transactions)
print(msft.insider_purchases)
# msft.insider_roster_holders

# # show recommendations
# msft.recommendations
# msft.recommendations_summary
# msft.upgrades_downgrades

# Show future and historic earnings dates, returns at most next 4 quarters and last 8 quarters by default. 
# Note: If more are needed use msft.get_earnings_dates(limit=XX) with increased limit argument.
print(msft.earnings_dates)

# # show options expirations
# msft.options

# show news
# print(msft.news)