import yfinance as yf

def get_earnings_date(ticker):
    """
    Get the earnings date of a company using its ticker symbol.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    str: The earnings date of the company.
    """
    # Create a Ticker object
    ticker_obj = yf.Ticker(ticker)

    # Get earnings information
    earnings_info = ticker_obj.calendar
    print(earnings_info)

    # Get earnings date
    earnings_date = earnings_info['Earnings Date'][0]

    return earnings_date

def get_most_recent_earnings_report(ticker):
    """
    Get the most recent quarterly earnings report of a company using its ticker symbol.

    Parameters:
    ticker (str): The ticker symbol of the company.

    Returns:
    pandas.Series: The most recent quarterly earnings report of the company.
    """
    # Create a Ticker object
    ticker_obj = yf.Ticker(ticker)

    # Get earnings information
    earnings_info = ticker_obj.quarterly_income_stmt

    # Get the most recent earnings report
    most_recent_earnings_report = earnings_info

    return most_recent_earnings_report

# Example usage:
print(get_most_recent_earnings_report("NFLX"))

# Example usage:
print(get_earnings_date("NFLX"))
