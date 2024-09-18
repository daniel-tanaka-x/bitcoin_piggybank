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
# Configuration Constants
# ==========================
BUY_AMOUNT = 30  # USD amount to buy in BTC when buy signal is triggered
BTC_THRESHOLD = 90  # USD threshold for triggering BTC withdrawal
RSI_PERIOD = 14  # RSI period to calculate
RSI_BUY_THRESHOLD = 20  # RSI value below which we consider buying BTC
FNG_EXTREME_FEAR_THRESHOLD = 25  # Fear and Greed Index value indicating extreme fear
WITHDRAW_THRESHOLD = 90  # BTC value in USD to trigger withdrawal
TIMEFRAME_HOURS = 24  # Number of hours for RSI analysis

# ==========================
# Helper Functions
# ==========================
def load_json(file_or_url):
    """Load JSON data from a file or URL."""
    if os.path.exists(file_or_url):
        with open(file_or_url, 'r') as f:
            return json.load(f)
    response = requests.get(file_or_url)
    if response.status_code == 200:
        return response.json()
    raise ValueError(f"Failed to load data from {file_or_url}")


def fetch_utxos(address):
    """Fetch UTXOs for a given Bitcoin address."""
    url = f"https://blockstream.info/api/address/{address}/utxo"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []


def generate_next_address(zpub, index):
    """Generate the next Bitcoin address from a given zpub using BIP84 (for a given index)."""
    bip84_ctx = Bip84.FromExtendedKey(zpub, Bip84Coins.BITCOIN)
    return bip84_ctx.Change(Bip44Changes.CHAIN_EXT).AddressIndex(index).PublicKey().ToAddress()


def get_unused_address(zpub, starting_index=0):
    """Generate addresses and find the first unused one by checking UTXOs."""
    index = starting_index
    while True:
        address = generate_next_address(zpub, index)
        utxos = fetch_utxos(address)
        if len(utxos) == 0:
            print(f"Unused address found at index {index}: {address}")
            return address, index
        index += 1


def fetch_rsi_signals(btc_data):
    """Fetch RSI signals over the last 24 hours of Bitcoin data."""
    last_24_hours = btc_data.tail(TIMEFRAME_HOURS)
    last_24_hours['RSI'] = talib.RSI(last_24_hours['Close'], timeperiod=RSI_PERIOD)
    buy_signals = last_24_hours[last_24_hours['RSI'] < RSI_BUY_THRESHOLD]
    print(f"RSI values for the last 24 hours:\n{last_24_hours['RSI']}")
    print(f"Buy signals (RSI < {RSI_BUY_THRESHOLD}) found: {len(buy_signals)}")
    return len(buy_signals)


def fetch_fear_and_greed_index():
    """Fetch the Fear and Greed Index and check for extreme fear."""
    fng_data = load_json("https://api.alternative.me/fng/?limit=1")['data'][0]
    fng_value = int(fng_data['value'])
    print(f"Fear and Greed Index: {fng_value}, Extreme fear: {fng_value <= FNG_EXTREME_FEAR_THRESHOLD}")
    return fng_value <= FNG_EXTREME_FEAR_THRESHOLD


def find_best_exchange_for_btc(exchanges):
    """Find the best exchange to buy BTC based on the lowest BTC/USDT price."""
    best_price = float('inf')
    best_exchange = None

    for exchange_name, exchange in exchanges.items():
        try:
            if not exchange.apiKey or not exchange.secret:
                print(f"Skipping {exchange_name} due to missing API credentials.")
                continue

            ticker = exchange.fetch_ticker('BTC/USDT')
            price = ticker['last']
            print(f"{exchange_name} offers BTC/USDT at {price} USD")

            if price < best_price:
                best_price = price
                best_exchange = exchange_name

        except Exception as e:
            print(f"Failed to fetch ticker from {exchange_name}: {e}")

    if best_exchange:
        print(f"Best exchange to buy BTC: {best_exchange} at {best_price} USD")
    return best_exchange, best_price


def execute_buy_order(exchange, buy_amount, best_price):
    """Execute a market buy order for BTC/USDT."""
    try:
        balance = exchange.fetch_balance()['total'].get('USDT', 0)
        print(f"Balance on exchange: {balance} USDT")

        if balance >= buy_amount:
            symbol = 'BTC/USDT'
            order = exchange.create_market_buy_order(symbol, buy_amount / best_price)
            print(f"Bought {buy_amount} USD worth of BTC on exchange")
        else:
            print(f"Insufficient balance to buy BTC.")
    except Exception as e:
        print(f"Failed to buy BTC: {e}")


def check_and_withdraw_btc(exchanges, zpub, btc_threshold, current_index):
    """Check balances and withdraw BTC if the value exceeds a threshold."""
    for exchange_name, exchange in exchanges.items():
        try:
            if not exchange.apiKey or not exchange.secret:
                print(f"Skipping {exchange_name} due to missing API credentials.")
                continue

            # Fetch BTC balance
            btc_balance = exchange.fetch_balance()['total'].get('BTC', 0)
            btc_value = btc_balance * exchange.fetch_ticker('BTC/USDT')['last']

            print(f"BTC balance on {exchange_name}: {btc_balance}, valued at {btc_value} USD")

            # Check if BTC value exceeds the threshold for withdrawal
            if btc_value >= btc_threshold:
                # Find a new unused address
                new_unused_address, current_index = get_unused_address(zpub, current_index)
                print(f"New unused Bitcoin address for withdrawal: {new_unused_address}")

                # Set up withdrawal parameters for specific exchanges
                withdrawal_params = {}
                if exchange_name == 'bybit':
                    withdrawal_params = {'chain': 'BTC', 'forceChain': 1, 'accountType': 'SPOT'}
                elif exchange_name == 'bitget':
                    withdrawal_params = {'transferType': 'on_chain', 'chain': 'BTC', 'size': str(btc_balance)}
                elif exchange_name == 'kucoin':
                    withdrawal_params = {'network': 'BTC'}
                elif exchange_name == 'mexc':
                    withdrawal_params = {'chain': 'BTC'}

                print(f"Attempting to withdraw from {exchange_name}...")
                print(f"BTC Balance: {btc_balance}, Address: {new_unused_address}, Params: {withdrawal_params}")

                # Execute the withdrawal
                try:
                    withdrawal = exchange.withdraw('BTC', btc_balance, new_unused_address, None, withdrawal_params)
                    print(f"Withdrew {btc_balance} BTC from {exchange_name} to {new_unused_address}")
                except Exception as e:
                    print(f"Failed to withdraw from {exchange_name}: {e}")
            else:
                print(f"BTC value on {exchange_name} is below the threshold for withdrawal: {btc_value} USD")
        except Exception as e:
            print(f"Failed to fetch balance on {exchange_name}: {e}")


# ==========================
# Main Bot Logic
# ==========================
def main():
    # Load API keys and zpub from JSON files
    api_keys = load_json("api_keys.json")
    zpub = load_json("zpub.json").get("zpub")

    # Setup exchange credentials
    EXCHANGES = {
        'bybit': ccxt.bybit({'apiKey': api_keys.get('bybit', {}).get('apiKey'), 'secret': api_keys.get('bybit', {}).get('secret')}),
        'bitget': ccxt.bitget({'apiKey': api_keys.get('bitget', {}).get('apiKey'), 'secret': api_keys.get('bitget', {}).get('secret'), 'password': api_keys.get('bitget', {}).get('password')}),
        'kucoin': ccxt.kucoin({'apiKey': api_keys.get('kucoin', {}).get('apiKey'), 'secret': api_keys.get('kucoin', {}).get('secret'), 'password': api_keys.get('kucoin', {}).get('password')}),
        'mexc': ccxt.mexc({'apiKey': api_keys.get('mexc', {}).get('apiKey'), 'secret': api_keys.get('mexc', {}).get('secret')}),
    }

    # Find unused Bitcoin address for receiving funds
    unused_address, current_index = get_unused_address(zpub)
    print(f"Using Bitcoin address (unused): {unused_address}")

    # Fetch Bitcoin price data for the last 5 days
    end_date = datetime.today()
    start_date = end_date - timedelta(days=5)
    btc = yf.download('BTC-USD', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval='1h')
    btc.index = btc.index.tz_convert('UTC')

    # Fetch RSI signals for the last 24 hours
    buy_signals = fetch_rsi_signals(btc)

    # Check the Fear and Greed Index
    extreme_fear = fetch_fear_and_greed_index()

    # Determine if a buy order should be placed
    if buy_signals > 0 or extreme_fear:
        best_exchange, best_price = find_best_exchange_for_btc(EXCHANGES)
        if best_exchange:
            execute_buy_order(EXCHANGES[best_exchange], BUY_AMOUNT, best_price)

    # Withdraw BTC if the balance exceeds $1000
    check_and_withdraw_btc(EXCHANGES, zpub, WITHDRAW_THRESHOLD, current_index)


if __name__ == "__main__":
    main()
