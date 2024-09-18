from twikit import Client
import os, asyncio
from json_make import Twitter_New_Json_edit


class Twitter_Client:
    def __init__(self):
        self.client = Client('en-US')

    async def load_client(self):
        if not os.path.isfile("./json/cookie.json"):
            print("Not set json file")
            os._exit(1)
        if not os.path.isfile("./json/cookie_edit.json"):
            Twitter_New_Json_edit()
        self.client.load_cookies('./json/cookie_edit.json')

    async def Twikit_Msg(self,user_id):
        tweets = await self.client.get_user_tweets(user_id, 'Tweets',count=2)
        print(tweets[0].id, tweets[1].id)
        return tweets[0].id, tweets[1].id

    async def Twikit_Id_From_Name(self,user_name):
        return self.client.get_user_by_screen_name(user_name)


# インスタンスを作成してからメソッドを呼び出す
client = Twitter_Client()
asyncio.run(client.load_client())
asyncio.run(client.Twikit_Msg())
