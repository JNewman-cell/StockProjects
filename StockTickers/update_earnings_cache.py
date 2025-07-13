import datetime
import logging
import sys
from CRUD_earnings_database import update_earnings_db_and_weekly_earnings
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def update_earnings_with_retry():
    try:
        update_earnings_db_and_weekly_earnings()
        logger.info("Successfully updated earnings database and weekly earnings")
    except Exception as e:
        logger.error(f"Error updating earnings data: {e}")
        raise

def main():
    try:
        # Run daily, but only process if it's Sunday
        if datetime.datetime.today().weekday() == 6:
            logger.info("Starting earnings data update process")
            update_earnings_with_retry()
            logger.info("Completed earnings data update process")
        else:
            logger.info("Not Sunday - skipping earnings update")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()