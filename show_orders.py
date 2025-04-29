from binance.client import Client
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import time
import sys
import platform
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for Windows
colorama.init()

# Load environment variables
load_dotenv()

# Initialize Binance client
client = Client(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_API_SECRET'),
    tld='us'
)

def clear_screen():
    """Clear the console screen"""
    if platform.system() == 'Windows':
        os.system('cls')
        print("\033[H\033[J", end="")  # Additional ANSI escape codes for Windows
    else:
        os.system('clear')

def show_current_status():
    """Show current trading status"""
    try:
        clear_screen()
        print(f"\n{Fore.YELLOW}=== DOGE Grid Trading Live Monitor ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        # Get current price
        ticker = client.get_symbol_ticker(symbol='DOGEUSDT')
        current_price = float(ticker['price'])
        print(f"\n{Fore.GREEN}Current DOGE Price: ${current_price:.5f}{Style.RESET_ALL}")
        
        # Get account balances
        account = client.get_account()
        doge_balance = next((asset for asset in account['balances'] if asset['asset'] == 'DOGE'), None)
        usdt_balance = next((asset for asset in account['balances'] if asset['asset'] == 'USDT'), None)
        
        print(f"\n{Fore.YELLOW}=== Balances ==={Style.RESET_ALL}")
        print(f"DOGE: {float(doge_balance['free']):.2f} (Free) / {float(doge_balance['locked']):.2f} (In Orders)")
        print(f"USDT: ${float(usdt_balance['free']):.2f} (Free) / ${float(usdt_balance['locked']):.2f} (In Orders)")
        
        # Calculate total value in USDT
        total_doge_value = (float(doge_balance['free']) + float(doge_balance['locked'])) * current_price
        total_usdt_value = float(usdt_balance['free']) + float(usdt_balance['locked'])
        total_value = total_doge_value + total_usdt_value
        print(f"{Fore.GREEN}Total Value: ${total_value:.2f} USDT{Style.RESET_ALL}")
        
        # Get open orders
        open_orders = client.get_open_orders(symbol='DOGEUSDT')
        
        print(f"\n{Fore.YELLOW}=== Open Orders ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}Buy Orders:{Style.RESET_ALL}")
        buy_orders = [order for order in open_orders if order['side'] == 'BUY']
        if buy_orders:
            for order in sorted(buy_orders, key=lambda x: float(x['price']), reverse=True):
                price = float(order['price'])
                distance = ((current_price - price) / price) * 100
                print(f"  {order['origQty']} DOGE @ ${price:.5f} ({distance:.1f}% from current)")
        else:
            print("  No buy orders")
        
        print(f"\n{Fore.CYAN}Sell Orders:{Style.RESET_ALL}")
        sell_orders = [order for order in open_orders if order['side'] == 'SELL']
        if sell_orders:
            for order in sorted(sell_orders, key=lambda x: float(x['price'])):
                price = float(order['price'])
                distance = ((price - current_price) / current_price) * 100
                print(f"  {order['origQty']} DOGE @ ${price:.5f} ({distance:.1f}% from current)")
        else:
            print("  No sell orders")
        
        # Get recent trades
        trades = client.get_my_trades(symbol='DOGEUSDT', limit=5)
        
        print(f"\n{Fore.YELLOW}=== Recent Trades ==={Style.RESET_ALL}")
        if trades:
            for trade in reversed(trades):
                time = datetime.fromtimestamp(trade['time']/1000)
                side = "Bought" if trade['isBuyer'] else "Sold"
                print(f"{time}: {side} {trade['qty']} DOGE @ ${float(trade['price']):.5f}")
        else:
            print("No recent trades")
        
        print(f"\n{Fore.RED}Press Ctrl+C to stop monitoring{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Next update in 5 seconds...{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"\n{Fore.RED}Error updating status: {e}{Style.RESET_ALL}")

def monitor_status():
    """Continuously monitor and display status"""
    try:
        while True:
            show_current_status()
            for i in range(5, 0, -1):
                time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopped monitoring.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        monitor_status()
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        input("Press Enter to exit...") 