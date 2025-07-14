from typing import List, Any

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json



async def fetch_ld_json(url: str,timeout:int = 0) -> list[list[Any]] | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(url)

        # ページ内の`<script type="application/ld+twitter_json">`を取得
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        ld_json_scripts = soup.find_all('script', type='application/ld+twitter_json')
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

            except Exception as e:
                print(f"エラー: {e}")
                return None
        await browser.close()
        return dictionary_list
#print(fetch_ld_json(""))