from binance.client import Client
import logging
import os
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN

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

def get_precision(symbol):
    """Get the precision for the symbol"""
    info = client.get_symbol_info(symbol)
    for filter in info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            step_size = float(filter['stepSize'])
            precision = len(str(step_size).split('.')[1].rstrip('0'))
            return precision
    return 8  # Default precision

def round_step_size(quantity, step_size):
    """Round quantity to the correct step size"""
    step_size = str(step_size)
    if '1' in step_size:
        precision = len(step_size.split('.')[1].rstrip('0'))
    else:
        precision = len(step_size.split('.')[1])
    return float(Decimal(str(quantity)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))

def convert_to_doge():
    try:
        # Get account information
        account = client.get_account()
        
        # Assets to convert (excluding DOGE)
        assets_to_convert = ['ADA', 'USDC', 'SOL', 'SHIB', 'USD']
        
        # First, convert everything to USDT
        for asset in account['balances']:
            if asset['asset'] in assets_to_convert:
                free_balance = float(asset['free'])
                if free_balance > 0:
                    logger.info(f"Converting {free_balance} {asset['asset']} to USDT...")
                    
                    # Create trading pair symbol
                    symbol = f"{asset['asset']}USDT"
                    
                    try:
                        # Get symbol info for precision
                        symbol_info = client.get_symbol_info(symbol)
                        step_size = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])
                        
                        # Calculate quantity to sell
                        quantity = round_step_size(free_balance, step_size)
                        
                        # Sell for USDT
                        order = client.create_order(
                            symbol=symbol,
                            side=Client.SIDE_SELL,
                            type=Client.ORDER_TYPE_MARKET,
                            quantity=quantity
                        )
                        logger.info(f"Converted {free_balance} {asset['asset']} to USDT")
                        
                    except Exception as e:
                        logger.error(f"Error converting {asset['asset']} to USDT: {e}")
        
        # Now convert all USDT to DOGE
        try:
            # Get USDT balance
            usdt_balance = next((asset for asset in account['balances'] if asset['asset'] == 'USDT'), None)
            if usdt_balance and float(usdt_balance['free']) > 0:
                free_usdt = float(usdt_balance['free'])
                logger.info(f"Converting {free_usdt} USDT to DOGE...")
                
                # Get DOGE price
                symbol = "DOGEUSDT"
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # Calculate DOGE quantity
                doge_quantity = free_usdt / current_price
                
                # Get symbol info for precision
                symbol_info = client.get_symbol_info(symbol)
                step_size = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])
                doge_quantity = round_step_size(doge_quantity, step_size)
                
                # Buy DOGE with USDT
                order = client.create_order(
                    symbol=symbol,
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=doge_quantity
                )
                logger.info(f"Converted {free_usdt} USDT to DOGE")
                
        except Exception as e:
            logger.error(f"Error converting USDT to DOGE: {e}")
        
        # Check final DOGE balance
        doge_balance = next((asset for asset in account['balances'] if asset['asset'] == 'DOGE'), None)
        if doge_balance:
            logger.info(f"Final DOGE Balance: {doge_balance['free']} DOGE")
        else:
            logger.info("No DOGE balance found")
            
    except Exception as e:
        logger.error(f"Error in conversion process: {e}")

if __name__ == "__main__":
    convert_to_doge() 