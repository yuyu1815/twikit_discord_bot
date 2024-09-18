import discord,os
from discord import app_commands
from dotenv import load_dotenv
import twitter_get
from discord.ext import tasks
import json_make
load_dotenv()
TOKEN = os.getenv('TOKEN')
CHANMEL_NAME = "PC4USHOP"
old_Msg1_id = 0
old_Msg2_id = 0

# いつもの呪文
intents = discord.Intents.default()
duscord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(duscord_client)

twitter_client = twitter_get.Twitter_Client()

check_time = 300
@duscord_client.event
async def on_ready():
  print('Login OK')
  await tree.sync()
  await twitter_client.load_client()
  loop.start()
# channelとtwitter_id設定
@tree.command(name='set', description='コマンドを実行したチャンネルでtwitterを表示します')
async def set(interaction: discord.Interaction,user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  #guild_id取得
  guild_id = interaction.guild_id
  # 名前からツイッターid取得
  twitter_id = await twitter_client.Twikit_Id_From_Name(user_name)
  #2銃登録防ぎ
  json_data = json_make.load_setting_json(guild_id)
  if json_data is not None:
    for json_channel_id in json_data["setting_channels"]:
      if channel_id in json_data["setting_channels"] and json_data["setting_channels"][channel_id] == twitter_id:
      return
  json_make.edit_setting_json(guild_id,channel_id,check_time,[channel_id],twitter_id)
  await interaction.response.send_message('設定完了')

# channelとtwitter_id削除
@tree.command(name='del', description='コマンドを実行したチャンネルで登録していたものを削除します')
async def set(interaction: discord.Interaction,user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  guild_id = interaction.guild_id
  await interaction.response.send_message('削除完了')

@tasks.loop(seconds=check_time)
async def loop():
  #送信先チャンネル指定
  channel = duscord_client.get_channel(int(CHANNEL_ID))
  # ツイート取得
  tweet_id,next_tweet_id = await twitter_client.Twikit_Msg(CHANMEL_NAME)
  # 同じ場合スキップ
  if(tweet_id == old_Msg1_id):
    return
  # 削除された時の対策用
  elif(tweet_id == old_Msg2_id):
    return
  # メッセージを更新
  old_Msg_id1 = tweet_id
  old_Msg_id2 = next_tweet_id
  # メッセージを送信
  url = f'https://fxtwitter.com/{CHANMEL_NAME}/status/{tweet_id}'
  print(url)
  await channel.send(url, silent=True)

duscord_client.run(TOKEN)