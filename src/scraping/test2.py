import requests
from bs4 import BeautifulSoup
import json
import sys,time


def extract_product_info(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        time.sleep(1)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        print(f" {soup}")
        # Extract product information
        product_info = {}
        # Name
        name_elem = soup.find('meta', property='og:title')['content']
        product_info['name'] = name_elem if name_elem else 'N/A'

        # Price
        price_elem = None
        product_info['price'] = price_elem if price_elem else 'N/A'

        # Shipping
        shipping_elem = soup.select_one('span.product-shipping-price')
        product_info['shipping'] = shipping_elem.text.strip() if shipping_elem else 'N/A'

        # Photo URL
        photo_elem = soup.find('meta', property='og:image')['content']
        product_info['photo_url'] = photo_elem if photo_elem else 'N/A'

        # Pretty print the JSON data
        print(json.dumps(product_info, indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while parsing the page: {e}", file=sys.stderr)
        sys.exit(1)
from playwright.async_api import async_playwright
import asyncio
import time


async def fetch_ld_json(url: str,timeout:int = 0) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # ページのロード完了を待たずにJavaScriptを実行
        await page.goto(url)

        # ページ内の`<script type="application/ld+json">`を取得
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        ld_json_scripts = soup.find_all('script', type='application/ld+json')
        #print(ld_json_scripts)
        dictionary_list = [[],[]]
        # JSONデータを辞書に変換
        if ld_json_scripts is None:
            return
        for script in ld_json_scripts:
            try:
                data_list = json.loads(script.string)

                # リストの各要素を処理
                for index, data_dict in enumerate(data_list):
                    print(f"要素 {index + 1}:")
                    for key in data_dict:
                        print(f"キー: {key}, 値: {data_dict[key]}")
                        dictionary_list[index].append(data_dict)

                    print()  # 各要素の間に空行を追加
            except Exception as e:
                print(f"エラー: {e}")
        #print(dictionary_list)
        await browser.close()
        return dictionary_list
if __name__ == "__main__":
    #extract_product_info("https://ja.aliexpress.com/item/1005005421916179.html")
    asyncio.run(fetch_ld_json("https://ja.aliexpress.com/item/1005005421916179.html"))