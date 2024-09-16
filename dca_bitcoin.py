import os
import json
import requests
import ccxt
import pandas as pd
import talib
import yfinance as yf
from datetime import datetime, timedelta
from bip_utils import Bip84, Bip84Coins, Bip44Changes

# ==========================
# Helper Functions
# ==========================
def load_json(file_or_url):
    """Load JSON data from a file or URL."""
    if os.path.exists(file_or_url):
        # Load from file
        with open(file_or_url, 'r') as f:
            return json.load(f)
    else:
        # Load from URL (for APIs)
        response = requests.get(file_or_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to load data from {file_or_url}")

# ==========================
# Address Generation Functions
# ==========================
def generate_first_address(zpub):
    """Generate the first Bitcoin address from a given zpub using BIP84 (index 0)."""
    bip84_ctx = Bip84.FromExtendedKey(zpub, Bip84Coins.BITCOIN)
    return bip84_ctx.Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()

# ==========================
# Trading Bot Logic
# ==========================

# Load API keys from JSON file
api_keys = load_json("api_keys.json")

# Define exchange credentials using loaded API keys
EXCHANGES = {
    'bybit': ccxt.bybit({'apiKey': api_keys['bybit']['apiKey'], 'secret': api_keys['bybit']['secret']}),
    'bitget': ccxt.bitget({'apiKey': api_keys['bitget']['apiKey'], 'secret': api_keys['bitget']['secret']}),
    'kucoin': ccxt.kucoin({'apiKey': api_keys['kucoin']['apiKey'], 'secret': api_keys['kucoin']['secret'], 'password': api_keys['kucoin']['password']}),
    'mexc': ccxt.mexc({'apiKey': api_keys['mexc']['apiKey'], 'secret': api_keys['mexc']['secret']}),
}

# Load zpub and generate the first address (index 0)
zpub = load_json("zpub.json").get("zpub")
first_address = generate_first_address(zpub)

print(f"Using Bitcoin address (index 0): {first_address}")

# Define the amount to buy and the BTC threshold for sending
BUY_AMOUNT = 300  # in USD
BTC_THRESHOLD = 1000  # in USD

# Step 1: Fetch Bitcoin data for the last 30 days (1-hour interval)
end_date = datetime.today()
start_date = end_date - timedelta(days=30)
btc = yf.download('BTC-USD', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval='1h')
btc.index = btc.index.tz_convert('UTC')

# Step 2: Calculate RSI and determine Buy/Sell zones
btc['RSI'] = talib.RSI(btc['Close'], timeperiod=14)
btc['Buy Zone'] = btc['RSI'] < 20
btc['Sell Zone'] = btc['RSI'] > 80

# Step 3: Fetch Fear and Greed Index
fng_data = load_json("https://api.alternative.me/fng/?limit=1")['data'][0]  # Get the most recent value
fng_value = int(fng_data['value'])

# Check if current RSI indicates a Buy Zone or if Fear and Greed Index indicates extreme fear
rsi_buy_signal = btc['Buy Zone'].iloc[-1]  # Check the last hour
extreme_fear = fng_value <= 25

# Step 4: Execute a buy order if there's a signal
if rsi_buy_signal or extreme_fear:
    for exchange_name, exchange in EXCHANGES.items():
        balance = exchange.fetch_balance()['total'].get('USDT', 0)
        if balance >= BUY_AMOUNT:
            # Place buy order for BTC
            try:
                symbol = 'BTC/USDT'
                order = exchange.create_market_buy_order(symbol, BUY_AMOUNT / exchange.fetch_ticker(symbol)['last'])
                print(f"Bought {BUY_AMOUNT} USD worth of BTC on {exchange_name}")
            except Exception as e:
                print(f"Failed to buy on {exchange_name}: {e}")

# Step 5: Check balances and send on-chain if the value exceeds $1000 to the same address
for exchange_name, exchange in EXCHANGES.items():
    try:
        btc_balance = exchange.fetch_balance()['total'].get('BTC', 0)
        btc_value = btc_balance * exchange.fetch_ticker('BTC/USDT')['last']

        if btc_value >= BTC_THRESHOLD:
            # Common withdrawal parameters
            coin = 'BTC'
            address = first_address
            amount = btc_balance

            # Exchange-specific handling
            withdrawal_params = {}
            if exchange_name == 'bybit':
                withdrawal_params = {'chain': 'BTC', 'forceChain': 1, 'accountType': 'SPOT'}
            elif exchange_name == 'bitget':
                withdrawal_params = {'transferType': 'on_chain', 'chain': 'BTC', 'size': str(btc_balance)}
            elif exchange_name == 'kucoin':
                withdrawal_params = {'network': 'BTC'}
            elif exchange_name == 'mexc':
                withdrawal_params = {'chain': 'BTC'}

            # Perform the withdrawal
            try:
                withdrawal = exchange.withdraw(coin, amount, address, None, withdrawal_params)
                print(f"Withdrew {btc_balance} BTC from {exchange_name} to {first_address}")
            except Exception as e:
                print(f"Failed to withdraw from {exchange_name}: {e}")
    except Exception as e:
        print(f"Failed to fetch balance on {exchange_name}: {e}")


print("Bot run complete.")
