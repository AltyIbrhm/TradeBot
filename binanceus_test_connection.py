from binance.client import Client
import os
from dotenv import load_dotenv
import requests

# Load API keys from .env
load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

print("Testing connection to Binance US...")

# Create client with tld='us' for Binance US
client = Client(api_key, api_secret, tld='us')

try:
    # Test basic endpoint directly first
    response = requests.get('https://api.binance.us/api/v3/ping')
    if response.status_code == 200:
        print("✓ Basic endpoint test successful")
    
    # Test authenticated endpoints
    print("\nTesting authenticated endpoints...")
    
    # Get account information
    account = client.get_account()
    print("\nConnection successful! Account info:")
    print(f"Can trade: {account['canTrade']}")
    print(f"Can withdraw: {account['canWithdraw']}")
    print(f"Can deposit: {account['canDeposit']}")
    
    # Get balance
    print("\nAccount balances:")
    for asset in account['balances']:
        free_balance = float(asset['free'])
        locked_balance = float(asset['locked'])
        if free_balance > 0 or locked_balance > 0:
            print(f"{asset['asset']}: Free = {free_balance}, Locked = {locked_balance}")
    
except requests.exceptions.RequestException as e:
    print(f"Network error: {str(e)}")
except Exception as e:
    print(f"Error: {str(e)}")
    if "APIError" in str(e):
        print("\nTroubleshooting steps:")
        print("1. Verify your API keys are correct")
        print("2. Check if your IP is whitelisted in your Binance US account")
        print("3. Ensure your Binance US account is fully verified")
        print("4. Try accessing Binance US website to confirm normal access")
        print("5. Check if you're using a VPN that might be blocked") 