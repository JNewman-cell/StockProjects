# StockProjects

### Summary of the Backend Functionality

The combined functionality of the provided code pieces supports a stock research web application by integrating data extraction, storage, and efficient search capabilities. Here’s an overview of how these components work together:

#### 1. **Fetching and Cleaning Market Capitalizations**
The initial step involves extracting stock ticker symbols and their corresponding market capitalizations from CSV files containing NASDAQ and NYSE data. Invalid entries with unavailable market caps are filtered out. This ensures only relevant and accurate ticker symbols are processed further.

#### 2. **Extracting Financial and Dividend Data**
For each valid stock ticker, detailed financial and dividend data is fetched using the Yahoo Finance API (`yfinance` library):
- **Financial Metrics:** Key financial ratios and metrics such as profit margins, payout ratio, dividend yield, cash flow, and market capitalization are extracted and stored.
- **Dividend Data:** Historical dividend data over the past 15 years is fetched and filtered to include only valid dividend payments.
- **Stock Info:** TTM values of important ratios and stock information along with recent financials.

#### 3. **Storing Data in SQLite Databases**
The extracted data is stored in two SQLite databases:
- **Financial Metrics Database:** This database stores comprehensive financial information, including company name, cash flow, earnings growth, revenue growth, PE ratios, and market cap.
- **Dividend Data Database:** This database keeps track of historical dividend payments, indexed by ticker and date.
- **Stock Info Database:** This database keeps track of TTM financial ratios and earnings growth, indexed by ticker.

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

### Why This Approach is Effective for the Stock Research Web Application

Using automated workflows to manage data extraction, cleaning, storage, and testing provides several key benefits that make this approach particularly effective for a stock research web application. Here’s an overview of why this method is advantageous:

#### 1. **Ensures Up-to-Date Information**

- **Scheduled Updates:** Regularly scheduled GitHub Actions workflows ensure that stock ticker and financial data are updated weekly. This keeps the web application's data current, which is crucial for users who rely on the latest market information for research and decision-making.
- **Automated Data Pulling:** The workflows automatically fetch new stock tickers and financial data from reliable sources like `yfinance`, ensuring that the application always has the most recent information without manual intervention.

#### 2. **Improves Data Quality and Consistency**

- **Data Cleaning:** Automated scripts clean the downloaded ticker data, filtering out invalid entries (e.g., tickers with 'N/A' market cap). This ensures that the data used in the application is accurate and reliable.
- **Validation:** Automated tests for the Trie data structure ensure that the autocomplete functionality works correctly, providing accurate and relevant suggestions to users.

#### 3. **Enhances Performance and User Experience**

- **Efficient Autocomplete:** The use of a Trie data structure for autocomplete allows for fast prefix matching, providing users with quick and relevant search results as they type. This enhances the overall user experience by making the application more responsive and easier to use.
- **Market Cap Sorting:** By sorting tickers based on market cap within the Trie, the application can prioritize more significant companies, which are likely of greater interest to users.

#### 4. **Streamlines Development and Maintenance**

- **Automated Workflows:** GitHub Actions automate the entire data pipeline—from pulling and cleaning data to updating the database and testing the Trie. This reduces the manual workload on developers and minimizes the risk of human error.
- **Version Control:** Committing updated data and databases to the GitHub repository ensures that all changes are tracked, and the application can be rolled back to a previous state if needed. This makes maintenance and debugging more straightforward.

#### 5. **Scalability and Flexibility**

- **Scalable Infrastructure:** Using GitHub Actions allows for scalable and flexible infrastructure management. The workflows can easily be adjusted to accommodate changes in data sources or processing requirements.
- **Modularity:** The separation of tasks into different scripts and workflows (e.g., data cleaning, Trie creation, database updates) makes the system modular. This modularity simplifies the process of updating individual components without affecting the entire pipeline.

#### 6. **Reliability and Robustness**

- **Continuous Integration:** The automated testing of the Trie ensures that any changes to the data or the codebase do not introduce errors. This continuous integration approach increases the reliability of the application.
- **Redundancy:** Regular updates and tests provide redundancy, ensuring that even if a particular update fails, the previous data remains intact and functional.

### Conclusion

This approach leverages the power of automation, scheduled tasks, and version control to create a robust, reliable, and user-friendly stock research web application. By ensuring that data is always current and accurate, and by automating time-consuming tasks, this method provides a solid foundation for delivering high-quality financial insights to users. The combination of efficient data processing, automated workflows, and regular testing enhances both the functionality and maintainability of the application.

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

## Scheduled Update of Earnings Cache:

[![Update Earnings Date Cache and DB (SQLite)](https://github.com/JNewman-cell/StockProjects/actions/workflows/earnings_cache.yml/badge.svg)](https://github.com/JNewman-cell/StockProjects/actions/workflows/earnings_cache.yml)
