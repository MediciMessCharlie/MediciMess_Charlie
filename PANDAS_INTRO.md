## Pandas Learning Plan: Analyzing Medici Bank Transactions

### Course Structure Overview

This plan uses the 20,000 historical transactions (1390-1440) as a rich, real-world dataset to teach Pandas fundamentals through progressively complex analyses.

---

### Module 1: Introduction & Data Loading 

**Learning Objectives:**

- Make a special git branch to hold all the changes to the dataset
- Understand what Pandas is and why it's essential for data engineering
- Load CSV and JSON data into DataFrames
- Explore basic DataFrame properties

**Hands-on Activities:**
1. **Load the transaction data**
   ```python
   import pandas as pd
   df = pd.read_csv('medici_transactions.csv')
   ```

2. **Initial exploration**
   - `df.head()`, `df.tail()`, `df.info()`, `df.describe()`
   - Understanding DataFrame structure vs the Python dictionaries in medici-banking.py
   - Compare loading CSV vs JSON formats

3. **Key questions to answer:**
   - How many transactions are there?
   - What columns exist?
   - What data types are present?
   - Are there any missing values?

---

### Module 2: Data Inspection & Cleaning 

**Learning Objectives:**
- Handle data types (especially dates and decimals)
- Identify and handle missing values
- Basic data validation

**Hands-on Activities:**
1. **Convert date strings to datetime objects**
   ```python
   df['date'] = pd.to_datetime(df['date'])
   ```

2. **Validate double-entry accounting**
   - Calculate total debits vs total credits
   - Verify the accounting equation holds (matching validate_transactions.py)

3. **Handle optional fields**
   - Investigate `credit_account_2` and `credit_amount_2`
   - Fill NaN values appropriately

4. **Data type optimization**
   - Convert currency amounts to proper numeric types
   - Categorical data for branches, types, counterparties

---

### Module 3: Basic Analysis & Aggregation 

**Learning Objectives:**
- Filter and select data
- Group by operations
- Basic aggregation functions

**Hands-on Activities:**
1. **Transaction type analysis**
   ```python
   df.groupby('type')['debit_amount'].agg(['count', 'sum', 'mean'])
   ```

2. **Branch performance**
   - Which branch processed the most transactions?
   - Which branch handled the largest total value?
   - Compare with the 33.1% Rome figure from documentation

3. **Time-based filtering**
   - Filter transactions during the Western Schism (1402-1420)
   - Find the Council of Constance ransom (May 29, 1415)
   - War financing during Florentine-Milanese wars

4. **Counterparty analysis**
   - Who were the most frequent customers?
   - Which counterparties had the largest transactions?

---

### Module 4: Time Series Analysis 

**Learning Objectives:**
- Work with datetime indices
- Resample and aggregate over time periods
- Identify trends and patterns

**Hands-on Activities:**
1. **Set datetime index**
   ```python
   df.set_index('date', inplace=True)
   ```

2. **Temporal aggregations**
   - Monthly transaction volumes
   - Quarterly revenue patterns
   - Yearly trends from 1390-1440

3. **Historical event analysis**
   - Spike in transactions during Council of Constance (1414-1418)
   - War financing patterns during conflict periods
   - Seasonal patterns in banking activity

4. **Moving averages and trends**
   - Calculate 90-day moving average of transaction volumes
   - Identify peak activity periods

---

### Module 5: Advanced Filtering & Queries 

**Learning Objectives:**
- Complex boolean indexing
- Query syntax
- Multi-condition filtering

**Hands-on Activities:**
1. **Find specific transaction types**
   - All papal deposits over 10,000 florins
   - War financing to Republic of Florence
   - Bills of exchange between specific branches

2. **Complex queries**
   ```python
   papal_war_loans = df.query('type == "war_financing" and counterparty.str.contains("Pope")')
   ```

3. **Account analysis**
   - Track all transactions affecting "Cash" account
   - Analyze loan repayments with interest components
   - Revenue vs expense patterns

---

### Module 6: Data Transformation & Feature Engineering 

**Learning Objectives:**
- Create calculated columns
- Apply custom functions
- Reshape data (pivot, melt, merge)

**Hands-on Activities:**
1. **Create derived metrics**
   - Total transaction value (debit + credits)
   - Extract interest amounts from loan repayments
   - Calculate transaction fees from bills of exchange

2. **Categorize transactions**
   - Create "transaction_size" categories (small/medium/large)
   - Flag high-value transactions (>10,000 florins)
   - Identify multi-account transactions

3. **Branch comparison tables**
   ```python
   pivot = df.pivot_table(
       values='debit_amount',
       index='branch',
       columns='type',
       aggfunc='sum'
   )
   ```

---

### Module 7: Data Visualization Integration 

**Learning Objectives:**
- Use Pandas plotting capabilities
- Prepare data for visualization libraries
- Tell stories with data

**Hands-on Activities:**
1. **Built-in Pandas plots**
   - Transaction volume over time (line plot)
   - Transaction type distribution (bar plot)
   - Branch comparison (horizontal bar)

2. **Prepare data for Matplotlib/Seaborn**
   - Aggregate data appropriately
   - Handle date formatting for plots
   - Create multi-series comparisons

3. **Historical narrative visualization**
   - Show the impact of the Council of Constance ransom
   - Visualize war financing spikes during conflicts
   - Compare papal banking (Rome) vs commercial (Florence)

---

### Module 8: Performance & Best Practices 

**Learning Objectives:**
- Optimize Pandas operations
- Memory management with large datasets
- Vectorization vs loops

**Hands-on Activities:**
1. **Memory optimization**
   ```python
   df.memory_usage(deep=True)
   # Optimize with categorical dtypes
   ```

2. **Efficient operations**
   - Compare `.apply()` vs vectorized operations
   - Use `.groupby()` efficiently
   - Avoid iterating with `.iterrows()`

3. **Chunking for larger datasets**
   - Read CSV in chunks
   - Process incrementally

---

### Capstone Project: Comprehensive Analysis 

**Project:** Create a complete analytical report on Medici Bank operations

**Requirements:**
1. **Financial Health Analysis**
   - Verify double-entry accounting across all transactions
   - Calculate net income by year
   - Track assets, liabilities, equity over time

2. **Business Intelligence**
   - Identify most profitable branches
   - Analyze customer segments (papal, merchant, noble)
   - Calculate average interest rates on loans

3. **Historical Insights**
   - Document impact of major historical events
   - Correlate war periods with financing activity
   - Trace growth of international branch network

4. **Deliverables**
   - Jupyter notebook with analysis
   - Summary visualizations
   - Written findings (2-3 pages)
   - Recommendations for "modern-day Medici Bank"

---

### **Bonus: Advanced Topics (Optional)**

**For advanced learners:**
1. **Merge with external data**
   - Historical inflation data
   - Convert florins to modern currency
   - GDP comparison

2. **Statistical analysis**
   - Correlation between transaction types
   - Outlier detection
   - Distribution fitting

3. **Export results**
   - Create summary CSV/Excel files
   - Generate HTML reports
   - Prepare data for databases

---

### **Assessment Strategy**

**Throughout the course:**
- Short coding exercises after each module
- Peer code reviews
- Progressive complexity in queries

**Final evaluation:**
- Capstone project (60%)
- Module quizzes (20%)
- Participation in code reviews (20%)

---

### **Required Tools & Setup**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # to start the venv

# Install required packages
pip install pandas jupyter matplotlib seaborn

# Launch Jupyter
jupyter notebook
```

---

### **Key Advantages of This Dataset**

1. **Real-world complexity**: Multi-account transactions, optional fields, various transaction types
2. **Historical context**: Makes learning memorable and engaging
3. **Large enough**: 20,000 rows provide meaningful aggregations
4. **Domain knowledge**: Links to accounting principles from medici-banking.py
5. **Validation built-in**: Can verify results against double-entry rules
6. **Multiple formats**: Practice with both CSV and JSON

This plan provides a very intensive introduction to Pandas for data engineering.
