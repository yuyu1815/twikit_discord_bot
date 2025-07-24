import asyncio
import json
import re
import time
import urllib.parse
from typing import Dict, Any, List, Optional

import httpx
from playwright.async_api import async_playwright, Route, BrowserContext
from playwright_stealth import stealth_async

# --- 設定項目 ---
PRODUCT_ID = "1005009475910159"  # 処理したい商品ID
USER_DATA_DIR = "./playwright_user_data"
HEADLESS_MODE = True


async def extract_cookies(context: BrowserContext) -> Dict[str, str]:
    """ブラウザコンテキストからaliexpress.comのクッキーを抽出する"""
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


async def send_api_request(client: httpx.AsyncClient, url: str, headers: Dict[str, str], cookies: Dict[str, str]) -> None:
    """APIリクエストを送信し、結果を処理する"""
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


async def capture_api_request(page, product_id: str) -> Optional[Dict[str, Any]]:
    """商品ページを開き、APIリクエストをキャプチャする"""
    product_url = f"https://ja.aliexpress.com/item/{product_id}.html"
    api_captured_event = asyncio.Event()
    captured_request = None
    
    # リクエストをインターセプトする関数
    async def on_route(route: Route):
        nonlocal captured_request
        request = route.request
        url = request.url
        
        # 不要なリソースはブロック
        if request.resource_type in ["image", "stylesheet", "font", "media"]:
            await route.abort()
            return
            
        # 目的のAPIを捕捉
        if "mtop.aliexpress.pdp.pc.query" in url and not api_captured_event.is_set():
            headers = extract_headers(request.headers)
            captured_request = {'url': url, 'headers': headers}
            
            # リクエストデータを表示
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            data_str = qs.get('data', [None])[0]
            if data_str:
                print("--- Captured API Request Data ---")
                print(json.dumps(json.loads(data_str), indent=2, ensure_ascii=False))
                print("-------------------------------")
                
            api_captured_event.set()
            
        await route.continue_()
    
    # ルーティングを設定
    await page.route("**/*", on_route)
    
    print(f"商品ページへのアクセスを開始します: {product_url}")
    try:
        # ページに移動（完了を待たない）
        await page.goto(product_url, wait_until="commit", timeout=60000)
        
        # スクロールをバックグラウンドで実行
        asyncio.create_task(page.mouse.wheel(0, 1000))
        
        print("目的のAPIリクエストを待機中...")
        # APIがキャプチャされるのを待つ
        await asyncio.wait_for(api_captured_event.wait(), timeout=15.0)
        
        # User-Agentを取得
        user_agent = await page.evaluate('() => navigator.userAgent')
        if captured_request:
            captured_request['user_agent'] = user_agent
            
    except asyncio.TimeoutError:
        print("APIリクエストの待機中にタイムアウトしました。")
    except Exception as e:
        print(f"ページのナビゲーション中にエラーが発生しました: {e}")
    
    return captured_request


async def process_product(context: BrowserContext, product_id: str) -> None:
    """商品ページを処理し、APIリクエストを実行する"""
    # 新しいページを開く
    page = await context.new_page()
    await stealth_async(page)
    
    try:
        # APIリクエストをキャプチャ
        captured_request = await capture_api_request(page, product_id)
        
        if not captured_request:
            print(f"商品ID {product_id} のAPIリクエストをキャプチャできませんでした。")
            return
            
        # クッキーを取得
        print("APIリクエストを送信します。")
        cookies = await extract_cookies(context)
        
        # APIリクエストを実行
        async with httpx.AsyncClient(http2=True) as client:
            if 'user_agent' in captured_request:
                client.headers.update({'user-agent': captured_request['user_agent']})
                
            await send_api_request(
                client, 
                captured_request['url'], 
                captured_request['headers'], 
                cookies
            )
    finally:
        await page.close()


async def main() -> None:
    """メイン処理：ブラウザを起動し、商品IDを処理する"""
    print(f"\n{'=' * 20} 商品ID: {PRODUCT_ID} の処理を開始 {'=' * 20}")
    start_time = time.time()
    
    async with async_playwright() as p:
        # ブラウザを起動
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=HEADLESS_MODE,
            slow_mo=50 if not HEADLESS_MODE else None,
            args=['--start-maximized']
        )
        
        try:
            # 商品を処理
            await process_product(context, PRODUCT_ID)
        finally:
            # ブラウザを閉じる
            await context.close()
    
    print(f"{'=' * 20} 商品ID: {PRODUCT_ID} の処理を終了 {'=' * 20}")
    print(f"実行時間: {time.time() - start_time:.2f}秒")
    print("\nすべての処理が完了しました。")


if __name__ == "__main__":
    asyncio.run(main())