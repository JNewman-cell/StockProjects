import datetime
from CRUD_earnings_database import update_earnings_db_and_weekly_earnings

def main():
    if datetime.datetime.today().weekday() == 6:
        update_earnings_db_and_weekly_earnings()

if __name__ == "__main__":
    main()