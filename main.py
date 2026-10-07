from src import config
from src.client import fetch_market_data

def print_summery(coins:list[dict])-> None:
    for coin in coins:
        print(
            f"{coin['market_cap_rank']}. {coin['name']}\n"
            
            f"{coin['symbol'].upper()}: ${coin['current_price']}"
        )

def main() -> None:
    config.validate_config()
    coins =  fetch_market_data(per_page=5)
    print(f"Fetched {len(coins)} Coins")
    print_summery(coins)


if __name__ == "__main__":
    main()

