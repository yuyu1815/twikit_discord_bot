import asyncio
import json
import re
import time
import urllib.parse
from typing import Dict, Any, List

import httpx
from playwright.async_api import async_playwright, Route, Page, BrowserContext
from playwright_stealth import stealth_async

# --- 設定項目 ---
# 処理したい商品IDをリストで指定
PRODUCT_IDS = ["1005009475910159", "1005007474187458", "1005007709496126"]
USER_DATA_DIR = "./playwright_user_data_async"
HEADLESS_MODE = True

# キャプチャしたリクエストを保存するリスト
captured_requests: List[Dict[str, Any]] = []

# キャプチャしたリクエストを保存するリスト
captured_requests: List[Dict[str, Any]] = []

# キャプチャしたリクエストを保存するリスト
captured_requests: List[Dict[str, Any]] = []


async def extract_cookies(context: BrowserContext) -> Dict[str, str]:
    """ブラウザコンテキストからaliexpress.comのクッキーを抽出する (非同期対応)"""
    cookies = await context.cookies()
    return {c['name']: c['value'] for c in cookies if 'aliexpress.com' in c.get('domain', '')}


def extract_headers(request_headers: Dict[str, str]) -> Dict[str, str]:
    """リクエストから不要なヘッダーを削除して抽出する"""
    headers_to_remove = ['content-length', 'host', 'connection', 'user-agent']
    return {k: v for k, v in request_headers.items() if k not in headers_to_remove}


def parse_jsonp(text: str) -> Any:
    """JSONP形式の文字列をパースしてPythonオブジェクトに変換する"""
    match = re.match(r'^[a-zA-Z0-9_]+\((.*)\)$', text.strip())
    return json.loads(match.group(1)) if match else None


async def send_request_async(client: httpx.AsyncClient, url: str, headers: Dict[str, str], cookies: Dict[str, str]):
    """httpxを使用して非同期でGETリクエストを送信し、結果を処理する"""
    try:
        response = await client.get(url, headers=headers, cookies=cookies, timeout=30)
        response.raise_for_status()
        data = parse_jsonp(response.text)
        if data:
            product_id = data.get('data', {}).get('productInfo', {}).get('productId')
            print(f"--- API Response (ProductID: {product_id}) ---")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("--------------------")
        else:
            print(f"JSONPのパースに失敗: {url}")
    except httpx.HTTPStatusError as e:
        print(f"HTTPエラー: {e.response.status_code} - URL: {url}")
    except Exception as e:
        print(f"リクエスト中にエラーが発生しました: {e} - URL: {url}")


async def on_route(route: Route, event: asyncio.Event):
    """リクエストをインターセプトして処理を振り分ける"""
    request = route.request
    url = request.url

    if request.resource_type in ["image", "stylesheet", "font", "media"]:
        await route.abort()
        return

    # 目的のAPIを捕捉し、まだキャプチャしていない場合のみ処理する
    if "mtop.aliexpress.pdp.pc.query" in url and not event.is_set():
        headers = extract_headers(request.headers)
        captured_requests.append({'url': url, 'headers': headers})

        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        data_str = qs.get('data', [None])[0]
        if data_str:
            print("--- Captured API Request Data ---")
            print(json.dumps(json.loads(data_str), indent=2, ensure_ascii=False))
            print("-------------------------------")

        event.set()

    await route.continue_()


async def process_product_page(context: BrowserContext, product_id: str):
    """単一の商品ページを処理し、APIリクエスト情報を収集・実行する"""
    global captured_requests
    captured_requests = []  # 前の商品のデータをクリア

    product_url = f"https://ja.aliexpress.com/item/{product_id}.html"
    page = await context.new_page()
    await stealth_async(page)

    api_captured_event = asyncio.Event()
    await page.route("**/*", lambda route: on_route(route, api_captured_event))

    print(f"商品ページへのアクセスを開始します: {product_url}")
    try:
        # ナビゲーションを開始するが、完了は待たない(commit)
        await page.goto(product_url, wait_until="commit", timeout=60000)
    except Exception as e:
        print(f"ページのナビゲーション開始に失敗しました: {e}")
        await page.close()
        return

    # スクロールをバックグラウンドで実行（完了を待たない）
    asyncio.create_task(page.mouse.wheel(0, 1000))

    print("目的のAPIリクエストを待機中...")
    user_agent = ""
    try:
        # APIがキャプチャされるのを待つ
        await asyncio.wait_for(api_captured_event.wait(), timeout=15.0)

        # ★ご要望の箇所: APIをキャプチャ後、即座にページの読み込みを停止
        print("APIリクエストをキャプチャしました。ページの読み込みを即時停止します。")
        await page.evaluate("window.stop();")

        user_agent = await page.evaluate('() => navigator.userAgent')
    except asyncio.TimeoutError:
        print("APIリクエストの待機中にタイムアウトしました。")
    finally:
        await page.close()

    if not captured_requests:
        print(f"商品ID {product_id} のAPIリクエストをキャプチャできませんでした。")
        return

    print(f"{len(captured_requests)}件のAPIリクエストを並列で送信します。")
    cookies = await extract_cookies(context)
    async with httpx.AsyncClient(http2=True) as client:
        if user_agent:
            client.headers.update({'user-agent': user_agent})

        tasks = [
            send_request_async(client, req['url'], req['headers'], cookies)
            for req in captured_requests
        ]
        await asyncio.gather(*tasks)


async def main():
    """メイン処理：ブラウザを起動し、各商品IDを処理する"""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=HEADLESS_MODE,
            slow_mo=50 if not HEADLESS_MODE else None,
            args=['--start-maximized']
        )

        for product_id in PRODUCT_IDS:
            print(f"\n{'=' * 20} 商品ID: {product_id} の処理を開始 {'=' * 20}")
            start_time = time.time()
            await process_product_page(context, product_id)
            print(f"{'=' * 20} 商品ID: {product_id} の処理を終了 {'=' * 20}")
            print(f"実行時間:{time.time() - start_time}")
            await asyncio.sleep(2)  # 次のリクエストへの短いインターバル

        print("\nすべての処理が完了しました。ブラウザを閉じます。")
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())