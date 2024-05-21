# StockProjects

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

### Summary of Backend Functionality

The integration of these automated workflows ensures the stock research web application maintains accurate, up-to-date information with minimal manual intervention. Here’s how each component contributes to the overall functionality:

1. **Data Extraction and Cleaning:** Automated scripts pull the latest ticker data and clean it, ensuring only valid entries are processed.
2. **Trie Autocomplete Creation:** The cleaned data is used to construct a Trie data structure, enabling efficient search and autocomplete functionality for users.
3. **Database Updates:** Dividend and financial data are fetched using `yfinance` and stored in SQLite databases, providing users with comprehensive and accurate financial insights.
4. **Automated Testing:** Regular tests ensure the Trie’s accuracy and functionality, maintaining the reliability of the search feature.
5. **Scheduled Execution:** GitHub Actions workflows run these processes on a regular schedule, keeping the data fresh and accurate without manual intervention.

By automating these processes, the application can deliver real-time, accurate stock information and a seamless user experience.

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
