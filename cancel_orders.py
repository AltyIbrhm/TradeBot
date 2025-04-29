from binance.client import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Binance client
client = Client(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_API_SECRET'),
    tld='us'  # For Binance US
)

# Cancel all open orders for DOGEUSDT
try:
    open_orders = client.get_open_orders(symbol='DOGEUSDT')
    for order in open_orders:
        client.cancel_order(
            symbol='DOGEUSDT',
            orderId=order['orderId']
        )
        print(f"Canceled order {order['orderId']}")
    print("Successfully canceled all open orders")
except Exception as e:
    print(f"Error canceling orders: {e}") 