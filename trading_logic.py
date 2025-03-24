import MetaTrader5 as mt5
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import numpy as np
import time
from datetime import datetime

# Connect to MT5
if not mt5.initialize():
    print("Failed to connect to MT5")
    quit()

print("Successfully logged into MT5")

# Fetch historical data from MT5
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 3, 23)
rates = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_H1, start_date, end_date)
if rates is None or len(rates) == 0:
    print("No data returned from MT5. Check symbol, timeframe, or date range.")
    mt5.shutdown()
    quit()

# Convert to DataFrame and inspect
df = pd.DataFrame(rates)
print("Columns in DataFrame:", df.columns.tolist())
print("First few rows of DataFrame:\n", df.head())

# Ensure 'time' column exists and convert to datetime
if 'time' not in df.columns:
    print("Error: 'time' column not found in data. Available columns:", df.columns.tolist())
    mt5.shutdown()
    quit()
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)

# Fetch external data using yfinance
eurusd = yf.Ticker("EURUSD=X")
external_data = eurusd.history(period="1mo")
print("External data from yfinance:")
print(external_data.tail())

# Prepare features for machine learning
df['returns'] = df['close'].pct_change()
df['ma5'] = df['close'].rolling(window=5).mean()
df['ma20'] = df['close'].rolling(window=20).mean()
df['signal'] = np.where(df['ma5'] > df['ma20'], 1, -1)  # 1 for BUY, -1 for SELL
df = df.dropna()

# Machine learning model
X = df[['returns', 'ma5', 'ma20']]
y = df['signal']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
print("Model accuracy:", model.score(X_test, y_test))

# Predict the latest signal
latest_data = X.iloc[-1:].copy()
signal = model.predict(latest_data)[0]
print("Predicted signal:", signal)

# Write signal to file with error handling
signal_text = "BUY" if signal == 1 else "SELL"
signal_file_path = "C:/Users/Latitude/AppData/Roaming/MetaQuotes/Terminal/Common/Files/trade_signal.txt"
try:
    with open(signal_file_path, "w") as f:
        f.write(signal_text)
    print(f"Signal written to file: {signal_text}")
except PermissionError as e:
    print(f"Permission error: {e}. Try running the script as administrator or closing MT5.")
except Exception as e:
    print(f"Failed to write signal file: {e}")

# Disconnect from MT5
mt5.shutdown()