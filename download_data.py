import yfinance as yf
import pandas as pd

msft = yf.Ticker("MNST")

# # get all stock info
# msft.info

# # get historical market data
# hist = msft.history(period="1mo")
# print(msft.dividends)
print(msft.income_stmt)
# print(msft.quarterly_income_stmt)
print(msft.balance_sheet)
print(msft.cashflow)

year_to_search = '2021'

# Convert column names to strings and then search for the year
df_columns_as_strings = msft.income_stmt.columns.astype(str)
index_of_year = None
for idx, col_name in enumerate(df_columns_as_strings):
    if year_to_search in col_name:
        index_of_year = idx
        break

print(index_of_year)
