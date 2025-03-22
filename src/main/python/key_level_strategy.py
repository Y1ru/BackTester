import pandas as pd
import cufflinks as cf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, time
from enum import Enum
from typing import List, Optional
from market_data_provider import MarketDataProvider  # Changed from yahoo_finance_fetcher

class Position:
    class Type(Enum):
        LONG = "LONG"
        SHORT = "SHORT"

    def __init__(self, entry_price: float, type: Type, entry_time: datetime):
        self.entry_price = entry_price
        self.type = type
        self.entry_time = entry_time
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[datetime] = None
        self.pnl: float = 0.0

    def close(self, exit_price: float, exit_time: datetime):
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.pnl = (self.exit_price - self.entry_price) if self.type == Position.Type.LONG \
            else (self.entry_price - self.exit_price)

class Trade:
    def __init__(self, position: Position):
        self.position = position
        self.stop_loss = position.entry_price - 20 if position.type == Position.Type.LONG \
            else position.entry_price + 20

    def should_stop_loss(self, current_price: float) -> bool:
        if self.position.type == Position.Type.LONG:
            return current_price <= self.stop_loss
        return current_price >= self.stop_loss

class KeyLevelStrategy:  # Changed from SPBacktester
    def __init__(self):
        # Initialize Cufflinks
        cf.go_offline()
        cf.set_config_file(world_readable=True, theme='pearl')
        self.positions: List[Position] = []
        self.current_trade: Optional[Trade] = None
        # Key levels for trading decisions (sorted in descending order)
        self.key_levels = sorted([6144, 6044, 5838, 5707, 5675, 5544, 5510], reverse=True)
        self.pending_signal: Optional[Position.Type] = None
        self.signal_level: Optional[float] = None
        self.trades_df = pd.DataFrame(columns=['DateTime', 'Price', 'Type', 'PnL'])

    def backtest(self, start_date: str, end_date: str = None, symbol: str = MarketDataProvider.SP500_SYMBOL):
        # Fetch data
        provider = MarketDataProvider()  # Changed from YahooFinanceFetcher
        df = provider.fetch_data(start_date, end_date, symbol)  # Changed 'fetcher' to 'provider'
        if df is None:
            return
    
        # Store original price data for visualization
        self.price_data = df.copy()
        
        # Process each bar
        for i, row in df.iterrows():
            current_time = row['datetime']
            current_price = row['close']
            prev_price = df.iloc[i-1]['close'] if i > 0 else current_price

            # Check for position exit conditions
            if self.current_trade:
                # Check if price hits another key level
                for level in self.key_levels:
                    if (self.current_trade.position.type == Position.Type.LONG and current_price >= level > self.current_trade.position.entry_price) or \
                       (self.current_trade.position.type == Position.Type.SHORT and current_price <= level < self.current_trade.position.entry_price):
                        self.close_position(current_price, current_time)
                        break

                # Check end of day exit
                if current_time.time() >= time(15, 55):  # 15:55 EST
                    self.close_position(current_price, current_time)

            # Check for entry conditions if no current position
            elif current_time.time() >= time(10, 00) and current_time.time() < time(15, 30):
                if self.pending_signal:
                    # Enter trade on the next bar after signal
                    self.open_position(current_price, self.pending_signal, current_time)
                    self.pending_signal = None
                    self.signal_level = None
                else:
                    # Look for new signals
                    for level in self.key_levels:
                        # Long signal: price breaks above a key level
                        if prev_price <= level < current_price:
                            self.pending_signal = Position.Type.LONG
                            self.signal_level = level
                            break
                        # Short signal: price breaks below a key level
                        elif prev_price >= level > current_price:
                            self.pending_signal = Position.Type.SHORT
                            self.signal_level = level
                            break

        # Print backtest results
        self.print_results()

    def open_position(self, price: float, type: Position.Type, time: datetime):
        position = Position(price, type, time)
        self.current_trade = Trade(position)
        self.positions.append(position)
        # Add trade to trades DataFrame
        self.trades_df = pd.concat([self.trades_df, pd.DataFrame({
            'DateTime': [time],
            'Price': [price],
            'Type': [type.value],
            'PnL': [0]
        })])

    def close_position(self, price: float, time: datetime):
        if self.current_trade:
            self.current_trade.position.close(price, time)
            # Update trades DataFrame
            self.trades_df.iloc[-1, self.trades_df.columns.get_loc('PnL')] = self.current_trade.position.pnl
            self.current_trade = None

    def visualize_results(self):
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                          vertical_spacing=0.03, subplot_titles=('Price Action', 'P&L'))

        # Add price line with purple color
        fig.add_trace(go.Scatter(
            x=self.price_data['datetime'],
            y=self.price_data['close'],
            name='Price',
            line=dict(color='purple')  # Changed from 'black' to 'purple'
        ), row=1, col=1)

        # Add key levels
        for level in self.key_levels:
            fig.add_hline(y=level, line_dash="dash", line_color="gray", row=1, col=1)

        # Add trade entries and exits
        for _, trade in self.trades_df.iterrows():
            color = 'green' if trade['Type'] == 'LONG' else 'red'
            fig.add_trace(go.Scatter(
                x=[trade['DateTime']],
                y=[trade['Price']],
                mode='markers',
                name=f"{trade['Type']} Entry",
                marker=dict(size=10, color=color, symbol='triangle-up' if trade['Type'] == 'LONG' else 'triangle-down')
            ), row=1, col=1)

        # Add cumulative P&L
        cum_pnl = self.trades_df['PnL'].cumsum()
        fig.add_trace(go.Scatter(
            x=self.trades_df['DateTime'],
            y=cum_pnl,
            name='Cumulative P&L',
            fill='tozeroy'
        ), row=2, col=1)

        # Update layout
        fig.update_layout(
            height=800,
            title_text="Backtest Results",
            showlegend=True
        )

        # Instead of fig.show(), return the figure
        return fig

    def print_results(self):
        total_trades = len(self.positions)
        winning_trades = sum(1 for p in self.positions if p.pnl > 0)
        total_pnl = sum(p.pnl for p in self.positions)

        print(f"\nBacktest Results:")
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Win Rate: {(winning_trades/total_trades*100):.2f}%" if total_trades > 0 else "N/A")
        print(f"Total P&L: {total_pnl:.2f} points")

        print("\nDetailed Trade List:")
        print("-" * 100)
        print(f"{'Trade #':<8} {'Type':<6} {'Entry Time':<20} {'Exit Time':<20} {'Entry Price':<12} {'Exit Price':<12} {'P&L':<10}")
        print("-" * 100)
        
        for i, position in enumerate(self.positions, 1):
            print(f"{i:<8} {position.type.value:<6} {position.entry_time.strftime('%Y-%m-%d %H:%M'):<20} "
                  f"{position.exit_time.strftime('%Y-%m-%d %H:%M'):<20} {position.entry_price:<12.2f} "
                  f"{position.exit_price:<12.2f} {position.pnl:<10.2f}")
        print("-" * 100)

def main():
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD) or press Enter for today: ").strip()
    symbol = input("Enter stock symbol or press Enter for S&P 500: ").strip()

    backtester = KeyLevelStrategy()  # Changed from SPBacktester
    backtester.backtest(
        start_date,
        end_date if end_date else None,
        symbol if symbol else MarketDataProvider.SP500_SYMBOL  # Changed from YahooFinanceFetcher
    )

if __name__ == '__main__':
    main()