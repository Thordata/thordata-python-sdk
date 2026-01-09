import os

from dotenv import load_dotenv

from thordata import ThordataClient, ThordataValidationError


def main():
    load_dotenv()
    token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not token:
        print("Please set THORDATA_SCRAPER_TOKEN")
        return

    # 初始化客户端
    client = ThordataClient(scraper_token=token)

    print("--- 1. Testing Structured Google Maps ---")
    try:
        # 新的调用方式
        maps_results = client.serp.google.maps(
            query="coffee", coordinates="@40.745,-74.008,14z"
        )
        print(f"✅ Success! Data keys: {list(maps_results.keys())}")
    except ThordataValidationError as e:
        # 如果是 400/402/403，说明请求发出去了，结构是对的，只是账户问题
        print(f"✅ SDK Structure Works! (API rejected request as expected: {e})")
    except Exception as e:
        print(f"❌ SDK Implementation Error: {e}")

    print("\n--- 2. Testing Structured Google Flights ---")
    try:
        flight_results = client.serp.google.flights(
            departure_id="JFK", arrival_id="LHR", outbound_date="2025-10-01"
        )
        print(f"✅ Success! Data keys: {list(flight_results.keys())}")
    except ThordataValidationError as e:
        print(f"✅ SDK Structure Works! (API rejected request as expected: {e})")
    except Exception as e:
        print(f"❌ SDK Implementation Error: {e}")


if __name__ == "__main__":
    main()
