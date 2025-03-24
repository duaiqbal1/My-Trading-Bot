from flask import Flask, render_template, request
import MetaTrader5 as mt5
import subprocess
import os
from datetime import datetime

app = Flask(__name__)

# Path to trading_logic.py
TRADING_LOGIC_PATH = "C:/TradingBott/trading_logic.py"
# Path to the signal file
SIGNAL_FILE_PATH = "C:/Users/Latitude/AppData/Roaming/MetaQuotes/Terminal/Common/Files/trade_signal.txt"
# Variable to track bot process
bot_process = None

@app.route('/')
def dashboard():
    # Check if running on Render (using an environment variable)
    if 'RENDER' in os.environ:
        # Static data for Render
        balance = 5000.0
        open_trades = 0
        trades = [
            {"time": "2025-03-01 10:00:00", "type": "BUY", "volume": 0.1, "profit": 50.0},
            {"time": "2025-03-02 12:00:00", "type": "SELL", "volume": 0.1, "profit": -20.0}
        ]
        total_profit = sum(trade["profit"] for trade in trades)
        latest_signal = "N/A"
        trade_times = [trade["time"] for trade in trades]
        trade_profits = [trade["profit"] for trade in trades]
        balance_values = [5000.0, 5050.0, 5030.0]  # Simulated balance over time
    else:
        # Local environment with MT5
        print("Attempting to initialize MT5...")
        if not mt5.initialize():
            print("MT5 initialization failed. Last error:", mt5.last_error())
            return "Failed to connect to MT5"

        # Verify MT5 connection
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            print("MT5 terminal not connected. Last error:", mt5.last_error())
            mt5.shutdown()
            return "MT5 terminal not connected"
        print("MT5 terminal connected:", terminal_info)

        # Verify account login
        account_info = mt5.account_info()
        if account_info is None:
            print("Failed to retrieve account info. Last error:", mt5.last_error())
            mt5.shutdown()
            return "Failed to retrieve account info"
        print("Account info retrieved:", account_info)

        # Get account balance
        balance = account_info.balance
        print("Account balance:", balance)

        # Get open trades
        open_trades = mt5.positions_total()
        print("Open trades:", open_trades)

        # Get historical trades with a broader date range
        from_date = datetime(2025, 1, 1)
        to_date = datetime(2025, 12, 31)
        history = mt5.history_deals_get(from_date, to_date)
        trades = []
        total_profit = 0
        trade_times = []
        trade_profits = []
        balance_values = [balance]  # Start with the current balance
        current_balance = balance
        if history:
            for deal in history:
                deal_time = datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M:%S')
                trades.append({
                    "time": deal_time,
                    "type": "BUY" if deal.type == mt5.DEAL_TYPE_BUY else "SELL",
                    "volume": deal.volume,
                    "profit": deal.profit
                })
                trade_times.append(deal_time)
                trade_profits.append(deal.profit)
                total_profit += deal.profit
                current_balance += deal.profit
                balance_values.append(current_balance)
            print("Historical trades retrieved:", len(trades), "trades")
        else:
            print("No historical trades found")
            trade_times = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            trade_profits = [0]
            balance_values = [balance]

        # Read the latest signal
        latest_signal = "N/A"
        try:
            with open(SIGNAL_FILE_PATH, "r") as f:
                latest_signal = f.read().strip()
        except Exception as e:
            print(f"Failed to read signal file: {e}")

        # Disconnect from MT5
        mt5.shutdown()
        print("MT5 connection closed")

    return render_template("dashboard.html", balance=balance, open_trades=open_trades, 
                          latest_signal=latest_signal, trades=trades, total_profit=total_profit,
                          trade_times=trade_times, trade_profits=trade_profits, balance_values=balance_values)

@app.route('/start_bot', methods=['POST'])
def start_bot():
    if 'RENDER' in os.environ:
        return "Bot control not available on Render"
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        bot_process = subprocess.Popen(["python", TRADING_LOGIC_PATH])
        return "Bot started"
    return "Bot is already running"

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    if 'RENDER' in os.environ:
        return "Bot control not available on Render"
    global bot_process
    if bot_process is not None and bot_process.poll() is None:
        bot_process.terminate()
        bot_process = None
        return "Bot stopped"
    return "Bot is not running"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # Set debug=False for production