# StockProjects

### Summary of the Backend Functionality

The combined functionality of the provided code pieces supports a stock research web application by integrating data extraction, storage, and efficient search capabilities. Here’s an overview of how these components work together:

#### 1. **Fetching and Cleaning Market Capitalizations**
The initial step involves extracting stock ticker symbols and their corresponding market capitalizations from CSV files containing NASDAQ and NYSE data. Invalid entries with unavailable market caps are filtered out. This ensures only relevant and accurate ticker symbols are processed further.

#### 2. **Extracting Financial and Dividend Data**
For each valid stock ticker, detailed financial and dividend data is fetched using the Yahoo Finance API (`yfinance` library):
- **Financial Metrics:** Key financial ratios and metrics such as profit margins, payout ratio, dividend yield, cash flow, and market capitalization are extracted and stored.
- **Dividend Data:** Historical dividend data over the past 15 years is fetched and filtered to include only valid dividend payments.

#### 3. **Storing Data in SQLite Databases**
The extracted data is stored in two SQLite databases:
- **Financial Metrics Database:** This database stores comprehensive financial information, including company name, cash flow, earnings growth, revenue growth, PE ratios, and market cap.
- **Dividend Data Database:** This database keeps track of historical dividend payments, indexed by ticker and date.

#### 4. **Efficient Search and Autocomplete with Trie Data Structure**
To facilitate quick and efficient searching of stock tickers based on user input, a Trie data structure is employed:
- **Insertion:** Ticker symbols are inserted into the Trie along with their market capitalizations.
- **Search and Suggestion:** When a user types a prefix, the Trie provides instant suggestions for matching tickers. It also returns tickers with the highest market capitalization for additional insights.

#### Integration Workflow
1. **Data Preparation:** 
    - The script reads cleaned CSV files to extract valid ticker symbols.
    - Financial and dividend data for each ticker is fetched using `yfinance`.
    - The extracted data is inserted into respective SQLite databases.

2. **Search and Suggestion:** 
    - The Trie is populated with tickers and market caps, enabling efficient autocomplete functionality.
    - Users receive instant suggestions as they type ticker symbols, enhancing the user experience.

3. **Database Operations:** 
    - Financial and dividend data are periodically updated to ensure the backend has the latest information.
    - The SQLite databases are queried to fetch and display relevant financial metrics and historical data as requested by the user.

### Benefits
- **Efficiency:** The Trie data structure ensures rapid search and autocomplete functionalities, providing a seamless user experience.
- **Data Integrity:** By filtering out invalid entries and updating data periodically, the application maintains high data accuracy and relevance.
- **Scalability:** The use of SQLite databases allows for efficient storage and retrieval of large volumes of financial and dividend data.
- **Comprehensive Insights:** Combining detailed financial metrics with historical dividend data offers users a holistic view of each stock's performance.

### Conclusion
Overall, this backend setup creates a robust and responsive infrastructure for a stock research web application, enabling users to access accurate financial data and receive real-time stock ticker suggestions efficiently.

### Summary of Automated Backend Processes for Stock Research Web Application

The stock research web application relies on a series of automated processes to fetch, clean, store, and test stock market data. These processes run on a scheduled basis using GitHub Actions, ensuring that the application maintains up-to-date and accurate data for users. Below is an overview of how these automated workflows function:

#### 1. **Pull and Clean Tickers and Create Trie Autocomplete**

**Workflow Overview:**
- **Schedule:** Runs every Sunday at 12:20 AM PST.
- **Purpose:** Fetch new stock tickers, clean the datasets, and update the Trie data structure for efficient autocomplete functionality.

**Steps:**
1. **Set Up Node.js and Python:** Ensure the environment has the necessary versions of Node.js and Python.
2. **Pull Ticker Data:** Download the latest NYSE and NASDAQ ticker symbols from a public repository.
3. **Clean Ticker Data:** Run scripts to clean the downloaded ticker datasets, removing any entries with invalid market caps.
4. **Create Trie:** Populate a Trie data structure with the cleaned ticker symbols and their market caps for fast search and autocomplete.
5. **Commit Updates:** Add and commit the cleaned datasets and the updated Trie data structure to the repository.

**Key Components:**
- **Node.js and Python Setup:** Ensures the environment is prepared for the execution of scripts.
- **Data Cleaning Scripts:** `clean_datasets.py` processes the downloaded tickers.
- **Trie Creation Script:** `create_Trie.py` constructs the Trie for autocomplete.
- **Version Control:** Updates are committed to the GitHub repository for consistency and version tracking.

#### 2. **Test Custom Trie Autocomplete**

**Workflow Overview:**
- **Schedule:** Runs every Sunday at 12:20 AM PST, right after the tickers are cleaned and Trie is created.
- **Purpose:** Verify the correctness of the Trie autocomplete functionality.

**Steps:**
1. **Set Up Node.js and Python:** Ensure the environment is set up correctly.
2. **Install Dependencies:** Install required Python packages.
3. **Run Tests:** Execute the `test_Trie.py` script to validate the Trie’s functionality.

**Key Components:**
- **Automated Testing:** Ensures the Trie data structure works as expected.
- **Test Script:** `test_Trie.py` includes unit tests to check for accurate prefix matching and market cap sorting.

#### 3. **Update Stock Dividends Database (SQLite)**

**Workflow Overview:**
- **Schedule:** Runs every Sunday at 1:00 AM PST.
- **Purpose:** Update the SQLite database with the latest dividend information for tracked stocks.

**Steps:**
1. **Set Up Node.js and Python:** Prepare the environment.
2. **Install Dependencies:** Ensure all required packages are installed.
3. **Update Dividend Data:** Run the `create_and_update_dividend_database.py` script to fetch and store the latest dividend data in the SQLite database.
4. **Commit Updates:** Add and commit the updated dividend database to the repository.

**Key Components:**
- **Dividend Data Script:** `create_and_update_dividend_database.py` fetches dividend data using `yfinance` and updates the SQLite database (`dividend_data.db`).
- **Version Control:** Keeps the dividend database updated and versioned within the repository.

## Scheduled Ticker Pulling, Cleaning, and Custom Trie Creation:

[![Pull and Clean Tickers and Make Trie Autocomplete](https://github.com/JNewman-cell/StockProjects/actions/workflows/tickers.yml/badge.svg)](https://github.com/JNewman-cell/StockProjects/actions/workflows/tickers.yml)

## Scheduled Trie Testing After Creation:

[![Test Custom Trie Autocomplete](https://github.com/JNewman-cell/StockProjects/actions/workflows/test_trie.yml/badge.svg)](https://github.com/JNewman-cell/StockProjects/actions/workflows/test_trie.yml)

## Scheduled Update of Database:

[![Update Stock Yearly Financials DB (SQLite)](https://github.com/JNewman-cell/StockProjects/actions/workflows/update_database.yml/badge.svg)](https://github.com/JNewman-cell/StockProjects/actions/workflows/update_database.yml)

## Scheduled Update of Dividend Database:

[![Update Stock Dividends DB (SQLite)](https://github.com/JNewman-cell/StockProjects/actions/workflows/update_dividend_database.yml/badge.svg)](https://github.com/JNewman-cell/StockProjects/actions/workflows/update_dividend_database.yml)

## Scheduled Update of TTM Database:

[![Update Stock TTM Financials and Ratios DB (SQLite)](https://github.com/JNewman-cell/StockProjects/actions/workflows/update_ttm_database.yml/badge.svg)](https://github.com/JNewman-cell/StockProjects/actions/workflows/update_ttm_database.yml)
