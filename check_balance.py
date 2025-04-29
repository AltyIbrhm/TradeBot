from binance.client import Client
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Binance client
client = Client(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_API_SECRET'),
    tld='us'  # For Binance US
)

def check_balances():
    try:
        # Get account information
        account = client.get_account()
        
        # Log all non-zero balances
        logger.info("=== Account Balances ===")
        for asset in account['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            if free > 0 or locked > 0:
                logger.info(f"{asset['asset']}:")
                logger.info(f"  Free: {free}")
                logger.info(f"  Locked in Orders: {locked}")
                logger.info(f"  Total: {free + locked}")
                logger.info("-------------------")
            
    except Exception as e:
        logger.error(f"Error checking balances: {e}")

if __name__ == "__main__":
    check_balances() 