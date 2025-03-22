import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz
from key_level_strategy import KeyLevelStrategy
from market_data_provider import MarketDataProvider
from key_level_strategy import KeyLevelStrategy
from market_data_provider import MarketDataProvider
from datetime import datetime, timedelta

st.set_page_config(page_title="Trading Strategy Backtester", layout="wide")

# Add this at the top of the page
# After the title and before the clock
st.title("Trading Strategy Backtester")

# Add disclaimer and attribution
st.markdown("""
<div style='background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
    <h4 style='color: #FF9F1C; margin: 0;'>⚠️ Data Source Information</h4>
    <p style='margin: 10px 0;'>This application uses Yahoo Finance API with the following limitations:</p>
    <ul>
        <li>Data is delayed by ~15 minutes</li>
        <li>5-minute interval data is limited to 60 days of history</li>
        <li>Real-time streaming updates every 5 seconds</li>
    </ul>
    <p style='color: #888; font-size: 0.9em; margin-top: 15px;'>Developed by Rui Feng Lin © 2024</p>
</div>
""", unsafe_allow_html=True)

# Add real-time clock
placeholder = st.empty()
def display_time():
    est_tz = pytz.timezone('US/Eastern')
    while True:
        with placeholder.container():
            est_time = datetime.now(est_tz)
            st.metric("Current Time (EST)", est_time.strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(1)

# Start clock in a separate thread
import threading
clock_thread = threading.Thread(target=display_time, daemon=True)
clock_thread.start()

# Add mode selection
mode = st.sidebar.radio("Select Mode", ["Backtest", "Real-time"])

# Update these import statements
from key_level_strategy import KeyLevelStrategy
from market_data_provider import MarketDataProvider

# Remove these old imports
# from sp_backtester import SPBacktester
# from yahoo_finance_fetcher import YahooFinanceFetcher

if mode == "Real-time":
    if 'real_time_data' not in st.session_state:
        st.session_state.real_time_data = pd.DataFrame()
    
    # Real-time streaming
    symbol = st.sidebar.text_input("Symbol", value=MarketDataProvider.SP500_SYMBOL)
    
    if st.sidebar.button("Start Streaming"):
        fetcher = MarketDataProvider()
        backtester = KeyLevelStrategy()
        
        while True:
            # Fetch latest data
            current_data = fetcher.fetch_realtime_data(symbol)
            if current_data is not None:
                st.session_state.real_time_data = pd.concat([st.session_state.real_time_data, current_data])
                
                # Update visualization
                backtester.price_data = st.session_state.real_time_data
                st.plotly_chart(backtester.visualize_results(), use_container_width=True)
                
            time.sleep(5)  # Update every 5 seconds
else:
    # Original backtest code
    # Sidebar inputs
    with st.sidebar:
        st.header("Backtest Parameters")
        
        # Date selection
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        ).strftime('%Y-%m-%d')
        
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        ).strftime('%Y-%m-%d')
        
        # Symbol selection
        symbol = st.text_input(
            "Symbol",
            value=MarketDataProvider.SP500_SYMBOL,
            help="Enter stock symbol (default: S&P 500)"
        )
        
        # Key levels input
        key_levels_str = st.text_area(
            "Key Levels (one per line)",
            value="6144\n6044\n5838\n5707\n5675\n5544\n5510"
        )
        key_levels = sorted([float(x.strip()) for x in key_levels_str.split('\n') if x.strip()], reverse=True)
        
        # Run backtest button
        run_backtest = st.button("Run Backtest")
    
    if run_backtest:
        # Initialize and run backtest
        backtester = KeyLevelStrategy()
        backtester.key_levels = key_levels  # Update key levels
        
        with st.spinner('Running backtest...'):
            backtester.backtest(start_date, end_date, symbol)
        
        # Display results in multiple columns
        col1, col2, col3 = st.columns(3)
        
        total_trades = len(backtester.positions)
        winning_trades = sum(1 for p in backtester.positions if p.pnl > 0)
        total_pnl = sum(p.pnl for p in backtester.positions)
        
        with col1:
            st.metric("Total Trades", total_trades)
        with col2:
            st.metric("Win Rate", f"{(winning_trades/total_trades*100):.1f}%" if total_trades > 0 else "N/A")
        with col3:
            st.metric("Total P&L", f"{total_pnl:.2f} points")
        
        # Display interactive chart
        st.plotly_chart(backtester.visualize_results(), use_container_width=True)
        
        # Display detailed trade list
        st.subheader("Detailed Trade List")
        
        trade_data = []
        for i, position in enumerate(backtester.positions, 1):
            trade_data.append({
                'Trade #': i,
                'Type': position.type.value,
                'Entry Time': position.entry_time,
                'Exit Time': position.exit_time,
                'Entry Price': position.entry_price,
                'Exit Price': position.exit_price,
                'P&L': position.pnl
            })
        
        trades_df = pd.DataFrame(trade_data)
        st.dataframe(trades_df, use_container_width=True)