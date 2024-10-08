import asyncio
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from faker import Faker
import json
import random


class AliexpressProductScraper:
    def __init__(self, product_id, reviews_count=20, filter_reviews_by='all', max_retries=3, timeout=60000):
        self.product_id = product_id
        self.reviews_count = reviews_count
        self.filter_reviews_by = filter_reviews_by
        self.faker = Faker()
        self.max_retries = max_retries
        self.timeout = timeout

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await self.set_random_user_agent(context)
                product_url = f"https://www.aliexpress.com/item/{self.product_id}.html"
                await self.navigate_with_retry(page, product_url)

                ali_express_data = await page.evaluate("() => runParams")

                data = ali_express_data.get('data', {})
                if not data:
                    raise ValueError("No data found")

                shipping = self.get_shipping_details(
                    data.get('webGeneralFreightCalculateComponent', {}).get('originalLayoutResultList', []))

                description_url = data.get('productDescComponent', {}).get('descriptionUrl')
                description_data = await self.get_description_data(page, description_url) if description_url else None

                reviews = await self.get_reviews()

                product_info = {
                    'title': data['productInfoComponent']['subject'],
                    'categoryId': data['productInfoComponent']['categoryId'],
                    'productId': data['productInfoComponent']['id'],
                    'quantity': {
                        'total': data['inventoryComponent']['totalQuantity'],
                        'available': data['inventoryComponent']['totalAvailQuantity'],
                    },
                    'description': description_data,
                    'orders': data['tradeComponent']['formatTradeCount'],
                    'storeInfo': self.get_store_info(data),
                    'ratings': self.get_ratings(data),
                    'images': data.get('imageComponent', {}).get('imagePathList', []),
                    'reviews': reviews,
                    'variants': self.get_variants(data),
                    'specs': data['productPropComponent']['props'],
                    'currencyInfo': data['currencyComponent'],
                    'originalPrice': self.get_price(data['priceComponent']['origPrice']),
                    'salePrice': self.get_price(data['priceComponent']['discountPrice']),
                    'shipping': shipping,
                }

                return product_info

            finally:
                await browser.close()

    async def set_random_user_agent(self, context):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        await context.set_extra_http_headers({"User-Agent": random.choice(user_agents)})

    async def navigate_with_retry(self, page, url):
        for attempt in range(self.max_retries):
            try:
                await page.goto(url, timeout=self.timeout)
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"Navigation failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    # ... (他のメソッドは変更なし) ...


async def main(product_id):
    scraper = AliexpressProductScraper(product_id)
    try:
        product_info = await scraper.scrape()
        print(json.dumps(product_info, indent=2))
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python script.py <product_id>")
        sys.exit(1)

    product_id = sys.argv[1]
    asyncio.run(main(product_id))