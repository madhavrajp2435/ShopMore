import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def get_prices(query):

    if not SERPAPI_KEY:
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "gl": "in",
        "hl": "en"
    }

    try:

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=20
        )

        data = response.json()

        products = []

        for item in data.get("shopping_results", []):

            price_text = str(item.get("price", ""))

            digits = "".join(
                c for c in price_text
                if c.isdigit() or c == "."
            )

            if not digits:
                continue

            products.append(
                {
                    "store": item.get("source", "Unknown"),
                    "title": item.get("title", ""),
                    "price": float(digits),
                    "link": item.get("product_link", "#")
                }
            )

        return sorted(
            products,
            key=lambda x: x["price"]
        )

    except Exception as e:

        print("SHOPPING ERROR:", e)

        return []