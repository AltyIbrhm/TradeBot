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

def prepare_balance():
    try:
        # Get current DOGE balance
        account = client.get_account()
        doge_balance = next((asset for asset in account['balances'] if asset['asset'] == 'DOGE'), None)
        
        if doge_balance:
            free_doge = float(doge_balance['free'])
            logger.info(f"Current DOGE balance: {free_doge}")
            
            # Calculate how much DOGE to convert (half of the balance)
            doge_to_convert = int(free_doge / 2)  # Round down to integer
            
            # Convert DOGE to USDT
            if doge_to_convert > 0:
                logger.info(f"Converting {doge_to_convert} DOGE to USDT...")
                
                order = client.create_order(
                    symbol='DOGEUSDT',
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=doge_to_convert
                )
                
                logger.info(f"Successfully converted {doge_to_convert} DOGE to USDT")
                
                # Get updated balances
                account = client.get_account()
                doge_balance = next((asset for asset in account['balances'] if asset['asset'] == 'DOGE'), None)
                usdt_balance = next((asset for asset in account['balances'] if asset['asset'] == 'USDT'), None)
                
                logger.info(f"New DOGE balance: {doge_balance['free']}")
                logger.info(f"New USDT balance: {usdt_balance['free']}")
                
            else:
                logger.error("Not enough DOGE to convert")
                
    except Exception as e:
        logger.error(f"Error preparing balance: {e}")

if __name__ == "__main__":
    prepare_balance() 