import asyncio
from traceback import print_tb

from twikit import Client
import os, sys,re,requests
from json_make import twitter_new_json_edit


class TwitterClient:
    def __init__(self):
        self.client = Client('en-US')

    async def load_client(self):
        if not os.path.isfile("twitter_json/cookie.json"):
            print("Not set twitter_json file")
            sys.exit()
        if not os.path.isfile("twitter_json/cookie_edit.json"):
            twitter_new_json_edit()
        self.client.load_cookies('twitter_json/cookie_edit.json')

    async def twikit_msg(self, user_name):
        try:
            user = await self.client.get_user_by_screen_name(user_name)
            tweets = await self.client.get_user_tweets(str(user.id), 'Tweets', count=2)
            return tweets[0].id, tweets[1].id
        except:
            #print(f"User '{user_name}' does not exist.")
            return None, None


    async def twikit_id_from_name(self, user_name):
        return await self.client.get_user_by_screen_name(user_name)

    async def get_retweet(self, target_tweet_id):
        tweet = await self.client.get_tweet_by_id(str(target_tweet_id))
        try:
            if tweet.is_quote_status or tweet.retweeted_tweet.id == target_tweet_id:
                return False
            else:
                return True
        except:
            return False
    # 画像がある場合URLを返す
    async def twitter_msg_get_url(self,msg_url):
        # msg_urlからtweet_idのみ取得
        tweet_id = None
        if "https://twitter.com" in msg_url:
            tweet_id = re.search(r'twitter\.com/.+/status/(\d+)', msg_url)
        elif "https://x.com" in msg_url:
            tweet_id = re.search(r'x\.com/.+/status/(\d+)', msg_url)

        if tweet_id is not None:
            tweet_id = tweet_id.group(1)
        else:
            return None
        tweet = await self.client.get_tweet_by_id(str(tweet_id))
        tweet_msg = tweet.full_text
        #url以外の文字列削除
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = re.findall(url_pattern, tweet_msg)
        # urlsは短縮のため展開
        urls = [requests.get(url).url for url in urls]
        for url in urls:
            if "https://twitter.com" in url or "https://x.com" in url:
                urls.remove(url)
        if urls:
            return urls
        else:
            return None
    #ユーザーが存在するか
    async def user_exist(self, user_name):
        try:
            user = await self.client.get_user_by_screen_name(user_name)
            return True
        except:
            return False

# インスタンスを作成してからメソッドを呼び出す
#client = TwitterClient()
#asyncio.run(client.load_client())
#print(asyncio.run(client.twitter_msg_get_url("https://x.com/lamrongol/status/1847566641955295344")))
#print(asyncio.run(client.get_retweet("1838858404955316541")))
#asyncio.run(client.twikit_msg())

