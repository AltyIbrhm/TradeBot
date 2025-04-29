from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
from dotenv import load_dotenv
import time
import logging
from datetime import datetime
import decimal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

class GridTradingBot:
    def __init__(self, symbol='DOGEUSDT', grid_levels=8, grid_range=0.01, order_size=12):
        # Load API keys
        load_dotenv()
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        
        # Initialize Binance client
        self.client = Client(self.api_key, self.api_secret, tld='us')
        
        # Trading parameters
        self.symbol = symbol
        self.grid_levels = grid_levels
        self.grid_range = grid_range  # 1% range for DOGE
        self.order_size = order_size  # $12 per order
        
        # Get symbol info for lot size
        self.symbol_info = self.client.get_symbol_info(symbol)
        self.lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', self.symbol_info['filters']))
        self.min_qty = float(self.lot_size_filter['minQty'])
        self.step_size = float(self.lot_size_filter['stepSize'])
        
        # Track current orders and profits
        self.active_orders = []
        self.grid_prices = []
        self.total_profit = 0
        
        logging.info(f"Initialized Grid Trading Bot for {symbol}")
        logging.info(f"Grid levels: {grid_levels}")
        logging.info(f"Grid range: {grid_range*100}%")
        logging.info(f"Order size: ${order_size}")
        logging.info(f"Minimum quantity: {self.min_qty}")
        logging.info(f"Step size: {self.step_size}")

    def format_quantity(self, quantity):
        """Format quantity according to Binance's lot size requirements"""
        precision = abs(decimal.Decimal(str(self.step_size)).as_tuple().exponent)
        quantity = max(self.min_qty, quantity)  # Ensure quantity is at least minimum
        return round(quantity - (quantity % self.step_size), precision)

    def get_current_price(self):
        """Get current price of the trading pair"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logging.error(f"Error getting current price: {e}")
            return None

    def calculate_grid_prices(self, current_price):
        """Calculate buy and sell prices for the grid"""
        grid_prices = []
        price_step = (current_price * self.grid_range) / (self.grid_levels // 2)
        
        # Calculate prices below current price (buy levels)
        for i in range(self.grid_levels // 2):
            price = current_price - (price_step * (i + 1))
            grid_prices.append(('BUY', price))
            
        # Calculate prices above current price (sell levels)
        for i in range(self.grid_levels // 2):
            price = current_price + (price_step * (i + 1))
            grid_prices.append(('SELL', price))
            
        return sorted(grid_prices, key=lambda x: x[1])  # Sort by price

    def cancel_all_orders(self):
        """Cancel all open orders for the symbol"""
        try:
            open_orders = self.client.get_open_orders(symbol=self.symbol)
            for order in open_orders:
                self.client.cancel_order(
                    symbol=self.symbol,
                    orderId=order['orderId']
                )
                logging.info(f"Cancelled order {order['orderId']}")
            return True
        except BinanceAPIException as e:
            logging.error(f"Error cancelling orders: {e}")
            return False

    def place_grid_orders(self):
        """Place initial grid of orders"""
        current_price = self.get_current_price()
        if not current_price:
            return False
            
        self.grid_prices = self.calculate_grid_prices(current_price)
        
        try:
            # Cancel any existing orders
            self.cancel_all_orders()
            
            # Get account balance
            account = self.client.get_account()
            doge_balance = next((float(asset['free']) for asset in account['balances'] if asset['asset'] == 'DOGE'), 0)
            usdt_balance = next((float(asset['free']) for asset in account['balances'] if asset['asset'] == 'USDT'), 0)
            
            logging.info(f"Available DOGE: {doge_balance}")
            logging.info(f"Available USDT: {usdt_balance}")
            
            # Place new grid orders
            for order_type, price in self.grid_prices:
                quantity = self.order_size / price
                formatted_quantity = self.format_quantity(quantity)
                
                # Check if we have enough balance
                if order_type == 'BUY' and usdt_balance < (self.order_size):
                    logging.warning(f"Skipping BUY order - insufficient USDT balance")
                    continue
                elif order_type == 'SELL' and doge_balance < formatted_quantity:
                    logging.warning(f"Skipping SELL order - insufficient DOGE balance")
                    continue
                
                order = self.client.create_order(
                    symbol=self.symbol,
                    side=order_type,
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=formatted_quantity,
                    price=round(price, 6)  # 6 decimals for DOGE
                )
                self.active_orders.append(order)
                logging.info(f"Placed {order_type} order: {formatted_quantity} {self.symbol} at {price}")
                
                # Update balances
                if order_type == 'BUY':
                    usdt_balance -= self.order_size
                else:
                    doge_balance -= formatted_quantity
                
            return True
        except BinanceAPIException as e:
            logging.error(f"Error placing grid orders: {e}")
            return False

    def calculate_profit(self, buy_price, sell_price, quantity):
        """Calculate profit for a completed grid trade"""
        buy_value = quantity * buy_price
        sell_value = quantity * sell_price
        profit = sell_value - buy_value
        return profit

    def check_orders(self):
        """Check and update order status"""
        try:
            open_orders = self.client.get_open_orders(symbol=self.symbol)
            filled_orders = [order for order in self.active_orders if order not in open_orders]
            
            for order in filled_orders:
                logging.info(f"Order filled: {order['side']} {order['quantity']} at {order['price']}")
                
                # Calculate and log profit if it's a SELL order
                if order['side'] == 'SELL':
                    profit = self.calculate_profit(
                        float(order['price']) / (1 + self.grid_range),  # Original buy price
                        float(order['price']),  # Sell price
                        float(order['quantity'])
                    )
                    self.total_profit += profit
                    logging.info(f"Trade profit: ${profit:.4f}, Total profit: ${self.total_profit:.4f}")
                
                # Place new order on the opposite side
                new_price = float(order['price'])
                if order['side'] == 'BUY':
                    new_price *= (1 + self.grid_range)
                else:
                    new_price *= (1 - self.grid_range)
                
                try:
                    new_order = self.client.create_order(
                        symbol=self.symbol,
                        side='SELL' if order['side'] == 'BUY' else 'BUY',
                        type='LIMIT',
                        timeInForce='GTC',
                        quantity=order['quantity'],
                        price=round(new_price, 6)
                    )
                    logging.info(f"Placed new order: {new_order['side']} at {new_price}")
                except BinanceAPIException as e:
                    logging.error(f"Error placing new order: {e}")
            
            self.active_orders = open_orders
            return True
        except BinanceAPIException as e:
            logging.error(f"Error checking orders: {e}")
            return False

    def run(self):
        """Main trading loop"""
        logging.info("Starting grid trading bot...")
        
        while True:
            try:
                # Place initial grid if no active orders
                if not self.active_orders:
                    if not self.place_grid_orders():
                        logging.error("Failed to place grid orders")
                        time.sleep(60)
                        continue
                
                # Check order status
                self.check_orders()
                
                # Wait before next check
                time.sleep(30)
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    # Initialize bot with parameters
    bot = GridTradingBot(
        symbol='DOGEUSDT',
        grid_levels=8,       # 8 levels (4 buy, 4 sell)
        grid_range=0.01,     # 1% range
        order_size=12        # $12 per order
    )
    
    # Start trading
    bot.run() 