import yfinance as yf
import pandas as pd
from datetime import datetime

class MarketDataProvider:  # Changed from YahooFinanceFetcher
    SP500_SYMBOL = '^GSPC'  # Default to S&P 500 index

    @staticmethod
    def fetch_data(start_date: str, end_date: str = None, symbol: str = SP500_SYMBOL, interval: str = '5m') -> pd.DataFrame:
        """
        Fetch S&P 500 data from Yahoo Finance
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            interval (str): Data interval (default: '5m')
            
        Returns:
            pd.DataFrame: DataFrame containing OHLCV data
        """
        try:
            # Convert string dates to datetime objects
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
            
            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval)
            
            if df.empty:
                print(f"No data available for the specified date range: {start_date} to {end_date}")
                return None
            
            # Reset index to make datetime a column
            df = df.reset_index()
            
            # Rename columns to match the expected format
            df = df.rename(columns={
                'Datetime': 'datetime',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return df
            
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            return None

    def fetch_realtime_data(self, symbol: str) -> pd.DataFrame:
        """Fetch real-time data for a single symbol"""
        try:
            ticker = yf.Ticker(symbol)
            current_data = ticker.history(period='1d', interval='1m').tail(1)
            
            if current_data.empty:
                return None
                
            # Format data to match existing structure
            current_data = current_data.reset_index()
            current_data = current_data.rename(columns={
                'Datetime': 'datetime',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return current_data
            
        except Exception as e:
            print(f"Error fetching real-time data: {str(e)}")
            return None

def main():
    # Example usage
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD) or press Enter for today: ").strip()
    symbol = input("Enter stock symbol or press Enter for S&P 500: ").strip()
    
    fetcher = YahooFinanceFetcher()
    data = fetcher.fetch_data(
        start_date,
        end_date if end_date else None,
        symbol if symbol else YahooFinanceFetcher.SP500_SYMBOL
    )
    
    if data is not None:
        print("\nFirst few rows of fetched data:")
        print(data.head())
        
        # Save the data to a CSV file with the symbol and today's date in the filename
        today_date = datetime.now().strftime('%Y%m%d')
        output_file = f'{symbol if symbol else "sp500"}_{today_date}_data.csv'
        data.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

if __name__ == '__main__':
    main()