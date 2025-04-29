from binance.client import Client
import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

# Initialize client
client = Client(api_key, api_secret, tld='us')

# Get current DOGE price
current_price = float(client.get_symbol_ticker(symbol='DOGEUSDT')['price'])

print(f"\nCurrent DOGE Price: ${current_price:.6f}")
print(f"\nGrid Levels (1% range):")
print(f"Current Price: ${current_price:.6f}")

print(f"\nSell Levels:")
for i in range(4):
    sell_price = current_price * (1 + 0.01 * (i+1))
    print(f"Level {i+1}: ${sell_price:.6f}")

print(f"\nBuy Levels:")
for i in range(4):
    buy_price = current_price * (1 - 0.01 * (i+1))
    print(f"Level {i+1}: ${buy_price:.6f}")

# Calculate order quantities
print(f"\nOrder Quantities (${12} per order):")
for i in range(4):
    sell_price = current_price * (1 + 0.01 * (i+1))
    buy_price = current_price * (1 - 0.01 * (i+1))
    sell_quantity = 12 / sell_price
    buy_quantity = 12 / buy_price
    print(f"\nLevel {i+1}:")
    print(f"Sell: {sell_quantity:.2f} DOGE at ${sell_price:.6f}")
    print(f"Buy: {buy_quantity:.2f} DOGE at ${buy_price:.6f}")

# Calculate total investment
total_investment = 12 * 8  # $12 per order × 8 orders
print(f"\nTotal Investment Required: ${total_investment}")
print(f"Buffer for Fees: ${100 - total_investment}") 