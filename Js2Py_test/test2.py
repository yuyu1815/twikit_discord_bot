import time, json, urllib.parse, requests, re
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

PRODUCT_ID = "1005009412352772"
PRODUCT_URL = f"https://ja.aliexpress.com/item/{PRODUCT_ID}.html"
USER_DATA_DIR = "./playwright_user_data"
captured_requests = []

def extract_cookies(context):
    return {c['name']: c['value'] for c in context.cookies() if 'aliexpress.com' in c.get('domain', '')}

def extract_headers(request):
    h = dict(request.all_headers())
    for k in ['content-length', 'host', 'connection']: h.pop(k, None)
    return h

def parse_jsonp(text):
    m = re.match(r'^[a-zA-Z0-9_]+\((.*)\)$', text.strip())
    return json.loads(m.group(1)) if m else None

def send_get(url, headers, cookies):
    r = requests.get(url, headers=headers, cookies=cookies, timeout=30)
    if r.status_code != 200:
        print(f"ステータス: {r.status_code}")
        return
    data = parse_jsonp(r.text)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def handle_popups(page):
    selectors = ["img[src*='close.png']", "div[class*='close']", "i[class*='close']",
                 "button[class*='close']", "div._24EHh", "a.next-dialog-close", ".btn-accept"]
    for sel in selectors:
        el = page.locator(sel).first
        if el.is_visible(timeout=2000): el.click(); time.sleep(1); break

def handle_route(route, context):
    req = route.request
    if "mtop.aliexpress.pdp.pc.query" not in req.url: return route.continue_()
    headers = extract_headers(req)
    captured_requests.append({'url': req.url, 'headers': headers})
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(req.url).query)
    data_str = qs.get('data', [None])[0]
    print(json.dumps(json.loads(data_str), indent=2, ensure_ascii=False))
    send_get(req.url, headers, extract_cookies(context))
    route.continue_()

def fetch():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False, slow_mo=50)
        page = context.new_page(); stealth_sync(page)
        page.route("**/mtop.aliexpress.pdp.pc.query/**", lambda r: handle_route(r, context))
        page.goto(PRODUCT_URL, wait_until="load", timeout=90000)
        time.sleep(3); handle_popups(page); page.mouse.wheel(0, 800); time.sleep(2)
        for i, r in enumerate(captured_requests, 1):
            send_get(r['url'], r['headers'], extract_cookies(context)); time.sleep(1)
        page.wait_for_timeout(10000); context.close()

def replay():
    for i, r in enumerate(captured_requests, 1):
        send_get(r['url'], r['headers'], {}); time.sleep(1)

if __name__ == "__main__":
    fetch()

