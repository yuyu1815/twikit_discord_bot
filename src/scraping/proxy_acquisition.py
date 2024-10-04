import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_web_proxy():
    proxies = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt').text.split('\n')
    return [proxy.strip() for proxy in proxies if proxy.strip()]


def check_single_proxy(proxy: str):
    proxy_dict = {
        "http": f"http://{proxy}"
    }
    try:
        start_time = time.time()
        response = requests.get("http://httpbin.org/ip", proxies=proxy_dict, timeout=1)
        elapsed_time = time.time() - start_time

        return (proxy, elapsed_time)
    except requests.exceptions.RequestException:
        return (proxy, None)


def check_proxies():
    proxies = get_web_proxy()
    print(len(proxies))
    results = {}

    with ThreadPoolExecutor(max_workers=min(40, len(proxies))) as executor:
        futures = [executor.submit(check_single_proxy, proxy) for proxy in proxies]
        for future in tqdm.tqdm(as_completed(futures), total=len(proxies)):
            proxy, elapsed_time = future.result()
            results[proxy] = elapsed_time

    return results


def create_driver_with_proxy(proxy):
    chrome_options = Options()
    chrome_options.add_argument(f'--proxy-server=http://{proxy}')
    chrome_options.add_argument("--headless=old")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def proxy_checker():
    proxy_results = check_proxies()
    sorted_proxies = sorted(
        [(proxy, elapsed_time) for proxy, elapsed_time in proxy_results.items() if
         elapsed_time is not None and elapsed_time < 0.7],
        key=lambda x: x[1]
    )
    proxy_list = [proxy for proxy, _ in sorted_proxies]
    return proxy_list


def check_proxies_with_driver(proxies):
    ok_proxy_list = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(create_driver_and_check_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(futures):
            proxy = futures[future]
            try:
                if future.result():
                    ok_proxy_list.append(proxy)
            except:
                pass

    return ok_proxy_list


def create_driver_and_check_proxy(proxy):
    driver = create_driver_with_proxy(proxy)
    try:
        driver.get('http://httpbin.org/ip')
        if '"origin":' in driver.page_source:
            print(f'Proxy {proxy} is working.')
            return True
        else:
            print(f'Proxy {proxy} is not working.')
            return False
    finally:
        driver.quit()

"""
# 実行例
proxies = proxy_checker()
ok_proxy_list = check_proxies_with_driver(proxies)
print(ok_proxy_list)
"""