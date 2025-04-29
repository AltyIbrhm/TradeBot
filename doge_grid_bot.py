from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
import logging
import os
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
import traceback
import sys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('doge_grid_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Binance client
client = Client(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_API_SECRET'),
    tld='us'  # For Binance US
)

# Trading parameters
SYMBOL = 'DOGEUSDT'
GRID_LEVELS = 4
GRID_SPACING = 0.01  # 1%
ORDER_SIZE_USDT = 12
TOTAL_INVESTMENT = 96  # $96 for orders, $4 buffer for fees

processed_orders = set()  # Keep track of processed order IDs

def get_current_price():
    """Get current DOGE price from Binance"""
    try:
        ticker = client.get_symbol_ticker(symbol=SYMBOL)
        return float(ticker['price'])
    except Exception as e:
        print(f"Error getting current price: {e}")
        return None

def calculate_grid_levels(current_price):
    """Calculate grid levels based on current price"""
    sell_levels = []
    buy_levels = []
    
    for i in range(1, GRID_LEVELS + 1):
        # Calculate sell levels (above current price)
        sell_price = current_price * (1 + (GRID_SPACING * i))
        sell_levels.append(f"{sell_price:.5f}")
        
        # Calculate buy levels (below current price)
        buy_price = current_price * (1 - (GRID_SPACING * i))
        buy_levels.append(f"{buy_price:.5f}")
    
    return sell_levels, buy_levels

def calculate_quantities(levels):
    """Calculate order quantities based on price levels"""
    quantities = []
    for price in levels:
        quantity = ORDER_SIZE_USDT / float(price)
        quantities.append(int(quantity))  # Round down to whole number
    return quantities

# Get current price and calculate grid levels
CURRENT_PRICE = get_current_price()
if CURRENT_PRICE is None:
    print("Failed to get current price. Exiting...")
    exit(1)

SELL_LEVELS, BUY_LEVELS = calculate_grid_levels(CURRENT_PRICE)
SELL_QUANTITIES = calculate_quantities(SELL_LEVELS)
BUY_QUANTITIES = calculate_quantities(BUY_LEVELS)

print(f"Current DOGE price: ${CURRENT_PRICE}")
print(f"Grid levels calculated:")
print(f"Buy levels: {BUY_LEVELS}")
print(f"Sell levels: {SELL_LEVELS}")
print(f"Buy quantities: {BUY_QUANTITIES}")
print(f"Sell quantities: {SELL_QUANTITIES}")

# Performance tracking
class PerformanceTracker:
    def __init__(self):
        self.start_time = datetime.now()
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_profit_usdt = 0
        self.errors = []
        self.last_balance_check = None
        self.initial_balance = None
        
    def add_trade(self, success, profit_usdt=0):
        self.total_trades += 1
        if success:
            self.successful_trades += 1
            self.total_profit_usdt += profit_usdt
        else:
            self.failed_trades += 1
    
    def add_error(self, error):
        self.errors.append({
            'timestamp': datetime.now(),
            'error': str(error),
            'traceback': traceback.format_exc()
        })
        
    def get_stats(self):
        uptime = datetime.now() - self.start_time
        return {
            'uptime': str(uptime),
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'total_profit_usdt': round(self.total_profit_usdt, 2),
            'success_rate': round(self.successful_trades / max(self.total_trades, 1) * 100, 2),
            'recent_errors': self.errors[-5:] if self.errors else []
        }

# Initialize performance tracker
performance = PerformanceTracker()

def check_api_health():
    """Check if Binance API is responsive"""
    try:
        # Try to get account info instead of system status
        client.get_account()
        return True
    except Exception as e:
        logger.error(f"Binance API health check failed: {e}")
        return False

def check_balance_threshold():
    """Check if balance is above minimum threshold"""
    try:
        account = client.get_account()
        doge_balance = next((asset for asset in account['balances'] if asset['asset'] == 'DOGE'), None)
        usdt_balance = next((asset for asset in account['balances'] if asset['asset'] == 'USDT'), None)
        
        if doge_balance and usdt_balance:
            total_doge = float(doge_balance['free']) + float(doge_balance['locked'])
            total_usdt = float(usdt_balance['free']) + float(usdt_balance['locked'])
            
            # Get current DOGE price
            ticker = client.get_symbol_ticker(symbol=SYMBOL)
            doge_price = float(ticker['price'])
            
            total_value_usdt = total_usdt + (total_doge * doge_price)
            
            if total_value_usdt < TOTAL_INVESTMENT * 0.8:  # Alert if below 80% of initial investment
                logger.warning(
                    f"Low balance warning: Total value: ${total_value_usdt:.2f} USDT\n"
                    f"DOGE: {total_doge:.2f}\n"
                    f"USDT: {total_usdt:.2f}"
                )
                
            return total_value_usdt
            
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        return None

def get_precision(symbol):
    """Get the precision for the symbol"""
    try:
        info = client.get_symbol_info(symbol)
        for filter in info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = float(filter['stepSize'])
                precision = len(str(step_size).split('.')[1].rstrip('0'))
                return precision
        return 8  # Default precision
    except Exception as e:
        logger.error(f"Error getting precision: {e}")
        raise

def round_step_size(quantity, step_size):
    """Round quantity to the correct step size"""
    try:
        step_size = str(step_size)
        if '1' in step_size:
            precision = len(step_size.split('.')[1].rstrip('0'))
        else:
            precision = len(step_size.split('.')[1])
        return float(Decimal(str(quantity)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))
    except Exception as e:
        logger.error(f"Error rounding step size: {e}")
        raise

def place_grid_orders():
    """Place initial grid orders, only as many as balance allows"""
    logger.info("Placing initial grid orders...")
    try:
        symbol_info = client.get_symbol_info(SYMBOL)
        step_size = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])
        placed_orders = []
        # Get balances
        account = client.get_account()
        doge_balance = next((float(asset['free']) for asset in account['balances'] if asset['asset'] == 'DOGE'), 0)
        usdt_balance = next((float(asset['free']) for asset in account['balances'] if asset['asset'] == 'USDT'), 0)
        # Place sell orders (use as much DOGE as possible)
        for i in range(GRID_LEVELS):
            quantity = round_step_size(SELL_QUANTITIES[i], step_size)
            if doge_balance >= quantity:
                try:
                    order = client.create_order(
                        symbol=SYMBOL,
                        side=Client.SIDE_SELL,
                        type=Client.ORDER_TYPE_LIMIT,
                        timeInForce=Client.TIME_IN_FORCE_GTC,
                        quantity=quantity,
                        price=str(SELL_LEVELS[i])
                    )
                    placed_orders.append(order)
                    doge_balance -= quantity
                    logger.info(f"Placed sell order: {quantity} DOGE at ${SELL_LEVELS[i]}")
                except BinanceAPIException as e:
                    logger.error(f"Error placing sell order: {e}")
            else:
                logger.warning(f"Skipping sell order {i+1} - insufficient DOGE balance for {quantity} DOGE")
        # Place buy orders (use as much USDT as possible)
        for i in range(GRID_LEVELS):
            quantity = round_step_size(BUY_QUANTITIES[i], step_size)
            required_usdt = quantity * float(BUY_LEVELS[i])
            if usdt_balance >= required_usdt:
                try:
                    order = client.create_order(
                        symbol=SYMBOL,
                        side=Client.SIDE_BUY,
                        type=Client.ORDER_TYPE_LIMIT,
                        timeInForce=Client.TIME_IN_FORCE_GTC,
                        quantity=quantity,
                        price=str(BUY_LEVELS[i])
                    )
                    placed_orders.append(order)
                    usdt_balance -= required_usdt
                    logger.info(f"Placed buy order: {quantity} DOGE at ${BUY_LEVELS[i]}")
                except BinanceAPIException as e:
                    logger.error(f"Error placing buy order: {e}")
            else:
                logger.warning(f"Skipping buy order {i+1} - insufficient USDT balance for {quantity} DOGE at ${BUY_LEVELS[i]}")
        if placed_orders:
            logger.info("Successfully placed all possible grid orders! Grid trading started.")
            return True
        else:
            logger.warning("No grid orders placed due to insufficient balances.")
            return False
    except Exception as e:
        logger.error(f"Error in place_grid_orders: {e}")
        return False

def check_orders():
    """Check for filled orders and replace them dynamically based on last fill price"""
    try:
        symbol_info = client.get_symbol_info(SYMBOL)
        step_size = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])
        min_price = float([f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]['minPrice'])
        min_notional = float([f for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'][0]['minNotional'])
        
        # Get account balances
        account = client.get_account()
        doge_balance = next((float(asset['free']) for asset in account['balances'] if asset['asset'] == 'DOGE'), 0)
        usdt_balance = next((float(asset['free']) for asset in account['balances'] if asset['asset'] == 'USDT'), 0)
        
        open_orders = client.get_open_orders(symbol=SYMBOL)
        all_orders = client.get_all_orders(symbol=SYMBOL, limit=100)
        
        # Filter out orders we've already processed
        filled_orders = [
            order for order in all_orders 
            if order['status'] == 'FILLED' 
            and order['orderId'] not in processed_orders
            and float(order['price']) > 0  # Skip invalid price orders
        ]

        for order in filled_orders:
            profit = 0
            try:
                order_id = order['orderId']
                if order_id in processed_orders:
                    continue
                
                logger.info(f"Processing new filled order: {order['side']} {order['origQty']} DOGE at ${order['price']}")
                filled_price = float(order['price'])
                quantity = float(order['origQty'])
                
                # Calculate profit for completed trades (approximate)
                if order['side'] == 'BUY':
                    # Place new sell order 1% above filled price
                    new_price = round(filled_price * (1 + GRID_SPACING), 5)
                    profit = 0  # Only realized after sell
                    side = Client.SIDE_SELL
                    # Check if we have enough DOGE balance
                    if doge_balance < quantity:
                        logger.warning(f"Insufficient DOGE balance ({doge_balance}) for sell order of {quantity} DOGE")
                        continue
                else:
                    # Place new buy order 1% below filled price
                    new_price = round(filled_price * (1 - GRID_SPACING), 5)
                    profit = quantity * (filled_price - new_price)
                    side = Client.SIDE_BUY
                    # Check if we have enough USDT balance
                    required_usdt = quantity * new_price
                    if usdt_balance < required_usdt:
                        logger.warning(f"Insufficient USDT balance (${usdt_balance}) for buy order of ${required_usdt}")
                        continue
                
                # Validate price
                if new_price < min_price:
                    logger.warning(f"New price ${new_price} is below minimum price ${min_price}")
                    continue
                
                # Round quantity to step size
                def round_step_size(qty, step):
                    return float(Decimal(str(qty)).quantize(Decimal(str(step)), rounding=ROUND_DOWN))
                rounded_qty = round_step_size(quantity, step_size)
                
                # Check minimum notional value
                if rounded_qty * new_price < min_notional:
                    logger.warning(f"Order value (${rounded_qty * new_price}) is below minimum (${min_notional})")
                    continue
                
                # Place the new order
                new_order = client.create_order(
                    symbol=SYMBOL,
                    side=side,
                    type=Client.ORDER_TYPE_LIMIT,
                    timeInForce=Client.TIME_IN_FORCE_GTC,
                    quantity=rounded_qty,
                    price=str(new_price)
                )
                logger.info(f"Placed new {side} order: {rounded_qty} DOGE at ${new_price}")
                performance.add_trade(True, profit)
                
                # Mark order as processed
                processed_orders.add(order_id)
                
                # Update balances
                if side == Client.SIDE_SELL:
                    doge_balance -= rounded_qty
                else:
                    usdt_balance -= (rounded_qty * new_price)
                
            except Exception as e:
                logger.error(f"Error processing filled order: {e}")
                performance.add_trade(False)
    except Exception as e:
        logger.error(f"Error in check_orders: {e}")

def print_daily_report():
    """Print daily performance report"""
    stats = performance.get_stats()
    report = (
        "📊 Daily Performance Report\n\n"
        f"Uptime: {stats['uptime']}\n"
        f"Total Trades: {stats['total_trades']}\n"
        f"Successful Trades: {stats['successful_trades']}\n"
        f"Failed Trades: {stats['failed_trades']}\n"
        f"Success Rate: {stats['success_rate']}%\n"
        f"Total Profit: ${stats['total_profit_usdt']}\n"
        "\nRecent Errors:\n"
    )
    
    for error in stats['recent_errors']:
        report += f"- {error['timestamp']}: {error['error']}\n"
    
    logger.info(report)

def main():
    logger.info("Starting DOGE Grid Trading Bot")
    
    logger.info(f"Initial investment: ${TOTAL_INVESTMENT}")
    logger.info(f"Grid levels: {GRID_LEVELS} above and below current price")
    logger.info(f"Grid spacing: {GRID_SPACING*100}%")
    logger.info(f"Order size: ${ORDER_SIZE_USDT}")
    
    # Initial setup
    if not check_api_health():
        logger.error("API health check failed. Exiting.")
        return
    
    # Store initial balance
    performance.initial_balance = check_balance_threshold()
    
    # Place initial grid orders
    if not place_grid_orders():
        logger.error("Failed to place initial orders. Exiting.")
        return
    
    last_daily_report = datetime.now()
    consecutive_errors = 0
    
    # Main loop
    while True:
        try:
            # Check API health periodically
            if not check_api_health():
                consecutive_errors += 1
                if consecutive_errors > 5:
                    logger.error("Too many consecutive errors. Bot needs attention!")
                    time.sleep(300)  # Wait 5 minutes before retrying
                continue
            
            # Reset error counter on successful operation
            consecutive_errors = 0
            
            # Check orders
            check_orders()
            
            # Check balance every hour
            if (not performance.last_balance_check or 
                datetime.now() - performance.last_balance_check > timedelta(hours=1)):
                check_balance_threshold()
                performance.last_balance_check = datetime.now()
            
            # Print daily report
            if datetime.now() - last_daily_report > timedelta(days=1):
                print_daily_report()
                last_daily_report = datetime.now()
            
            # Sleep for 1 minute
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            performance.add_error(e)
            time.sleep(60)

if __name__ == "__main__":
    main() 