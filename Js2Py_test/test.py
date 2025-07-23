import requests
import time
import json
import hashlib
import random
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# --- 設定項目 ---
PRODUCT_ID = "1005008694023094"
PRODUCT_URL = f"https://ja.aliexpress.com/item/{PRODUCT_ID}.html"
# ブラウザのセッション情報（Cookieなど）を保存するフォルダ
USER_DATA_DIR = "./playwright_user_data"

# --- ボット検出回避のための設定 ---
PROXY_SERVER = None
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def handle_popups(page):
    """
    ページ上のポップアップやモーダルを検知して閉じる。
    """
    # 検出対象となるポップアップの閉じるボタンのセレクタリスト
    close_selectors = [
        "img[src*='close.png']",
        "div[class*='close']",
        "i[class*='close']",
        "button[class*='close']",
        "div._24EHh",  # GDPR/Cookie同意バナーの閉じるボタンの例
        "a.next-dialog-close",
    ]

    print("ポップアップをチェックしています...")
    for selector in close_selectors:
        try:
            # セレクタが表示されるのを短時間待つ
            close_button = page.locator(selector).first
            if close_button.is_visible(timeout=2000):
                print(f"ポップアップを検出しました ({selector})。閉じます。")
                close_button.click()
                time.sleep(1)  # クリック後の待機
        except Exception:
            # ボタンが見つからなくてもエラーにせず、次のセレクタへ
            pass


def get_dynamic_cookies_stealth(url: str) -> dict:
    """
    永続的なブラウザセッションを使い、ボット検出を回避してCookieを取得する。
    """
    print("永続セッションを使用してブラウザを起動します...")

    with sync_playwright() as p:
        # 永続的なコンテキストを起動（指定したフォルダにセッション情報が保存される）
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,  # デバッグのため、ブラウザを表示
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            proxy={"server": PROXY_SERVER} if PROXY_SERVER else None,
            java_script_enabled=True,
            args=['--start-maximized']
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Stealthプラグインを適用
        stealth_sync(page)

        try:
            print(f"ページにアクセス中: {url}")
            # 'domcontentloaded' を使用して、基本的なページ構造の読み込み完了を待つ
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # ページ読み込み後の待機とポップアップ処理
            time.sleep(random.uniform(3, 5))
            handle_popups(page)

            print("ページのセキュリティチェックを通過させるための操作を実行します...")
            page.mouse.wheel(0, random.randint(500, 1000))
            time.sleep(random.uniform(2, 4))

            cookies = context.cookies()
            if not any(c['name'] == '_m_h5_tk' for c in cookies):
                print("警告: _m_h5_tk Cookieがまだ生成されていません。ページをリロードします。")
                page.reload(wait_until="domcontentloaded")
                time.sleep(5)
                cookies = context.cookies()

            print("Cookieの取得に成功しました。")

        except Exception as e:
            print(f"ページの読み込みまたはCookieの取得中にエラーが発生しました: {e}")
            page.screenshot(path='error_screenshot.png')
            print("エラー発生時のスクリーンショットを 'error_screenshot.png' に保存しました。")
            return {}
        finally:
            print("ブラウザを閉じます。")
            context.close()

    return {cookie['name']: cookie['value'] for cookie in cookies}


def generate_signature(cookies: dict, data_payload: str) -> tuple[str, str]:
    print("リクエスト署名(sign)を生成します...")
    m_h5_tk = cookies.get("_m_h5_tk")
    if not m_h5_tk:
        raise ValueError("_m_h5_tk Cookieが見つかりません。")
    token = m_h5_tk.split('_')[0]
    t = str(int(time.time() * 1000))
    app_key = "12574478"
    message = f"{token}&{t}&{app_key}&{data_payload}"
    sign = hashlib.md5(message.encode('utf-8')).hexdigest()
    print(f"生成された署名: {sign}")
    return sign, t


def fetch_product_data():
    cookies = get_dynamic_cookies_stealth(PRODUCT_URL)
    if not cookies:
        print("Cookieが取得できなかったため、処理を中断します。")
        return

    ext_data = {"site": "jpn", "host": "ja.aliexpress.com"}
    data = {
        "productId": PRODUCT_ID, "_lang": "ja_JP", "_currency": "JPY", "country": "JP",
        "clientType": "pc", "ext": json.dumps(ext_data)
    }
    data_payload_str = json.dumps(data)

    try:
        sign, t = generate_signature(cookies, data_payload_str)
    except ValueError as e:
        print(e)
        return

    api_url = "https://acs.aliexpress.com/h5/mtop.aliexpress.pdp.pc.query/1.0/"
    params = {
        'jsv': '2.5.1', 'appKey': '12574478', 't': t, 'sign': sign,
        'api': 'mtop.aliexpress.pdp.pc.query', 'v': '1.0', 'type': 'originaljsonp',
        'dataType': 'originaljsonp', 'callback': 'mtopjsonp1', 'data': data_payload_str
    }
    cookie_header_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    headers = {
        'User-Agent': random.choice(USER_AGENTS), 'Referer': PRODUCT_URL,
        'Cookie': cookie_header_str
    }

    print("\nAPIにリクエストを送信しています...")
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        raw_text = response.text.strip()
        if raw_text.startswith(params['callback'] + '(') and raw_text.endswith(')'):
            json_str = raw_text[len(params['callback']) + 1:-1]
        else:
            raise ValueError("レスポンスが予期したJSONP形式ではありません。")
        result_data = json.loads(json_str)
        print("\n--- 商品情報取得成功 ---")
        print(json.dumps(result_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n処理中にエラーが発生しました: {e}")
        if 'response' in locals():
            print("取得した生データ:", response.text)


if __name__ == "__main__":
    fetch_product_data()
