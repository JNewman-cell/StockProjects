import datetime
from CRUD_ex_dividend_database import update_ex_dividends_db_and_weekly_dividends

def main():
    if datetime.datetime.today().weekday() == 6:
        update_ex_dividends_db_and_weekly_dividends()

if __name__ == "__main__":
    main()