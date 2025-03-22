# Trading Strategy Backtester

A Python-based trading strategy backtester that implements a key-level breakout strategy for the S&P 500 index.

## Features

- Real-time and historical data analysis
- Key level breakout strategy implementation
- Interactive visualization with Plotly
- Performance metrics calculation
- Streamlit web interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BackTester.git
cd BackTester

2. Install dependencies:
```bash
pip install -r requirements.txt
 ```

## Usage
Run the Streamlit dashboard:

```bash
cd src/main/python
streamlit run trading_dashboard.py
 ```

## Strategy Details
The backtester implements a key-level breakout strategy:

- Monitors price action around predefined key levels
- Generates long signals on upward breakouts
- Generates short signals on downward breakouts
- Includes end-of-day exit rules
- Implements basic stop-loss mechanisms
## Data Source
Uses Yahoo Finance API with the following limitations:

- Data is delayed by ~15 minutes
- 5-minute interval data is limited to 60 days of history
- Real-time streaming updates every 5 seconds
## License
MIT License

## Author
Rui Feng Lin
