from twikit import Client
import os, sys
from json_make import twitter_new_json_edit


class TwitterClient:
    def __init__(self):
        self.client = Client('en-US')

    async def load_client(self):
        if not os.path.isfile("./json/cookie.json"):
            print("Not set json file")
            sys.exit()
        if not os.path.isfile("./json/cookie_edit.json"):
            twitter_new_json_edit()
        self.client.load_cookies('./json/cookie_edit.json')

    async def twikit_msg(self, user_name):
        try:
            user = await self.client.get_user_by_screen_name(user_name)
            tweets = await self.client.get_user_tweets(str(user.id), 'Tweets', count=2)
            return tweets[0].id, tweets[1].id
        except:
            print(f"User '{user_name}' does not exist.")
            return None, None

    async def twikit_id_from_name(self, user_name):
        return await self.client.get_user_by_screen_name(user_name)


# インスタンスを作成してからメソッドを呼び出す
"""
client = Twitter_Client()
asyncio.run(client.load_client())
asyncio.run(client.Twikit_Msg())
"""