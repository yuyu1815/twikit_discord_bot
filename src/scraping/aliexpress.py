from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import platform

from src.scraping.proxy_acquisition import proxy_checker


# 感謝　https://qiita.com/nyanyacyan/items/6b5e7e8de194a4a0a93b https://qiita.com/vZke/items/2ffdefc774e56145e093
class aliexpress:
    def __init__(self,proxy):
        self.options = webdriver.ChromeOptions()
        #uiがある場合動作が遅いがUIが見えないやつを使う
        #もしかしたらバグがあるかも 未来の自分設定を作ってください
        if (platform.system() == 'Windows' or platform.system() == 'Darwin'):
            #3秒
            # 普通とnewには白く表示があるためそれを防ぐため
            print(platform.system())
            #self.options.add_argument("--headless=old")
            self.options.add_argument("--headless=new")
        else:
            #0.6秒
            self.options.add_argument("--headless=new")
            print(platform.system())
        self.options.set_capability('pageLoadStrategy', 'eager')
        self.options.add_argument("--hide-scrollbars")
        self.options.add_argument("--disable-gpu")
        #self.options.add_argument(f"--proxy-server=http://{proxy}")
        prefs = {"profile.managed_default_content_settings.images": 2}
        self.options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=self.options)


    def get_data(self,url):
        # ブラウザを開く
        try:
            self.driver.get(url)
        except:
            self.driver.close()
            return None
        #読み込みが終わるまで待機
        sell_title = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "title--wrap--UUHae_g"))
        )
        # 商品名
        sell_title_text = sell_title.text
        #画像
        try:
            # 画像の場合
            img_url = self.driver.find_element(By.CLASS_NAME, "magnifier--image--EYYoSlr").get_attribute("src")
        except:
            # ビデオの場合
            img_url = self.driver.find_element(By.CLASS_NAME, "video--video--lsI7y97").get_attribute("poster")

        # セール前価格
        sell_price_original_text = self.driver.find_element(By.CLASS_NAME, "price--currentPriceText--V8_y_b5").text
        try:
            # セール後価格
            sell_price_text = self.driver.find_element(By.CLASS_NAME, "price--originalText--gxVO5_d").text
            # セールオフ率
            sell_price_off_text = self.driver.find_element(By.CLASS_NAME, "price--discount--Y9uG2LK").text
        except:
            sell_price_text = ""
            sell_price_off_text = ""
            pass
        # 在庫数
        sell_count_text = self.driver.find_element(By.CLASS_NAME, "quantity--info--jnoo_pD").text
        # 発送日時
        sell_postage_text = self.driver.find_element(By.CLASS_NAME, "dynamic-shipping-contentLayout").text
        # 配送料
        sell_skip_time_text = self.driver.find_element(By.CLASS_NAME, "dynamic-shipping-line").text
        #星の個数
        try:
            sell_star_text = self.driver.find_element(By.CLASS_NAME, "reviewer--rating--xrWWFzx").text
        except:
            sell_star_text = ""
        try:
            sell_review_text = self.driver.find_element(By.CLASS_NAME, "reviewer--reviews--cx7Zs_V").text
        except:
            sell_review_text = ""

        try:
            #アリエク保障マーク
            choice= self.driver.find_element(By.CLASS_NAME, "choice-mind--box--fJKH05M")
            choice_text = choice.text
        except:
            choice_text = ""
            pass
        return sell_title_text,img_url,sell_price_text,sell_price_original_text,sell_price_off_text,sell_count_text,sell_postage_text,sell_skip_time_text,choice_text,sell_star_text,sell_review_text


#proxy_list = proxy_checker()
proxy_list = ['35.72.118.126:80', '46.51.249.135:3128', '52.196.1.182:80', '35.76.62.196:80', '35.79.120.242:3128', '43.201.121.81:80', '13.208.56.180:80', '43.202.154.212:80', '13.208.245.138:8081', '54.248.238.110:80', '43.200.77.128:3128', '3.37.125.76:3128', '20.210.113.32:8123', '15.207.35.241:1080', '65.1.244.232:80', '103.49.202.250:80', '161.34.40.38:3128', '161.34.40.37:3128', '65.1.244.232:1080', '13.234.24.116:3128', '3.108.115.48:1080', '35.154.78.253:1080', '65.1.244.232:3128', '35.154.71.72:1080', '13.126.184.76:3128', '54.83.185.141:3128', '103.127.1.130:80', '184.169.154.119:80', '116.80.60.151:3128', '140.227.228.202:10101', '40.76.69.94:8080', '65.1.40.47:1080', '13.56.192.187:3128', '34.205.61.74:3128', '140.227.204.70:3128', '34.122.187.196:80', '44.226.167.102:1080', '13.126.184.76:1080', '89.116.191.51:80', '143.42.66.91:80', '54.212.22.168:1080', '107.175.179.52:80', '34.215.74.117:3128', '161.34.40.111:3128', '35.161.172.205:3128', '116.80.47.22:3128', '54.212.22.168:80', '3.12.144.146:3128', '20.205.61.143:8123', '175.208.59.76:8080', '86.109.3.27:10011', '160.86.242.23:8080', '50.62.183.223:80', '13.40.239.130:1080', '35.178.104.4:80', '35.178.104.4:3128', '162.223.90.130:80', '3.122.84.99:80', '20.205.61.143:80', '3.141.217.225:80', '13.38.176.104:3128', '18.228.149.161:80', '13.37.89.201:3128', '13.36.104.85:80']
print(proxy_list)
str_s = []
count = 100
while proxy_list:
    try:
        aex = aliexpress(proxy_list[0])
        str_s = aex.get_data("https://ja.aliexpress.com/item/1005005421916179.html")
    except:
        count -=1
        pass
    #del proxy_list[0]
    #if str_s:
    #    break
print(count)
print(str_s)

