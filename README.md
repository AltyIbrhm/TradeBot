# DOGE Grid Trading Bot

A Python-based grid trading bot for DOGE/USDT trading pair on Binance. The bot implements a grid trading strategy with dynamic price levels and order management.

## Features

- Dynamic grid level calculation based on current market price
- Automatic order placement and management
- Balance tracking and validation
- Performance monitoring and reporting
- Live dashboard for monitoring trades
- Error handling and recovery

## Requirements

- Python 3.7+
- Binance API credentials
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AltyIbrhm/TradeBot.git
cd TradeBot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Binance API credentials:
     ```
     BINANCE_API_KEY=your_api_key
     BINANCE_API_SECRET=your_api_secret
     ```
   - Optionally adjust trading parameters in `.env`:
     ```
     GRID_LEVELS=4
     GRID_SPACING=0.01
     ORDER_SIZE_USDT=12
     TOTAL_INVESTMENT=96
     ```

## Usage

1. Start the trading bot:
```bash
python doge_grid_bot.py
```

2. Monitor trades in a separate terminal:
```bash
python show_orders.py
```

## Configuration

The bot can be configured in two ways:

1. Through the `.env` file (recommended for sensitive settings)
2. By modifying the following parameters in `doge_grid_bot.py`:

- `GRID_LEVELS`: Number of grid levels above and below current price
- `GRID_SPACING`: Percentage spacing between grid levels
- `ORDER_SIZE_USDT`: Size of each order in USDT
- `TOTAL_INVESTMENT`: Total investment amount in USDT

## Security Notes

- Never share your `.env` file or API credentials
- The `.env` file is excluded from git for security
- Use `.env.example` as a template for your configuration

## License

MIT License

## Disclaimer

This bot is for educational purposes only. Use at your own risk. Cryptocurrency trading involves significant risk of loss. 