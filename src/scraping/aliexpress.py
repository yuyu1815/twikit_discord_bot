from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import platform
# 感謝　https://qiita.com/nyanyacyan/items/6b5e7e8de194a4a0a93b https://qiita.com/vZke/items/2ffdefc774e56145e093
class aliexpress:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        #uiがある場合動作が遅いがUIが見えないやつを使う
        #もしかしたらバグがあるかも 未来の自分設定を作ってください
        if (platform.system() == 'Windows' or platform.system() == 'Darwin'):
            #3秒
            # 普通とnewには白く表示があるためそれを防ぐため
            print(platform.system())
            #self.options.add_argument("--headless=old")
        else:
            #0.6秒
            self.options.add_argument("--headless=new")
            print(platform.system())
        self.options.set_capability('pageLoadStrategy', 'eager')
        self.options.add_argument("--hide-scrollbars")
        self.options.add_argument("--disable-gpu")
        prefs = {"profile.managed_default_content_settings.images": 2}
        self.options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=self.options)


    def get_data(self,url):
        # ブラウザを開く
        self.driver.get(url)
        time.sleep(100)
        #読み込みが終わるまで待機
        sell_title = WebDriverWait(self.driver, 20).until(
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

aep = aliexpress()
aep.get_data("https://ja.aliexpress.com/item/1005005421916179.html")
