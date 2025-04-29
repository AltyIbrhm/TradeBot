from binance.client import Client
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Binance client
client = Client(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_API_SECRET'),
    tld='us'  # For Binance US
)

# Get symbol info
symbol_info = client.get_symbol_info('DOGEUSDT')

# Print filters
print("DOGEUSDT Trading Rules:")
print(json.dumps(symbol_info['filters'], indent=2)) 