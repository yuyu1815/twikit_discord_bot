import discord,os,time
from discord import app_commands
from dotenv import load_dotenv
import twitter_get,json_make
from discord.ext import tasks

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

old_time = time.time()

check_time = 1
@duscord_client.event
async def on_ready():
  print('Login OK')
  await tree.sync()
  await twitter_client.load_client()
  loop.start()

#discordとメッセ時に送信
async def messege_send(interaction,msg):
  print(msg)
  await interaction.response.send_message(msg)
  return
# 以下コマンド類
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
  for i in range(len(json_data["setting_channels"])):
    if json_data["setting_channels"][i] == channel_id and json_data["twitter_user_ids"][i] == twitter_id:
      # 登録済み処理
      await messege_send(interaction, 'すでに設定しているため追加できませんでした')
      return

  # 登録完了
  json_data["setting_channels"].append(channel_id)
  json_data["twitter_user_ids"].append(twitter_id)

  json_make.edit_setting_json(guild_id, json_data["cool_down_time"], json_data["setting_channels"],json_data["twitter_user_ids"])
  await interaction.response.send_message('設定完了')

# channelとtwitter_id削除
@tree.command(name='del', description='コマンドを実行したチャンネルで登録していたものを削除します')
async def set(interaction: discord.Interaction,user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  guild_id = interaction.guild_id
  # 名前からツイッターid取得
  twitter_id = await twitter_client.Twikit_Id_From_Name(user_name)
  json_data = await json_make.load_setting_json(guild_id)

  if json_data is None:
    # 読み込み失敗
    await messege_send(interaction, '設定jsonを読み込むことができませんでした')
    return
  else:
    for i in range(len(json_data["setting_channels"])):
      if json_data["setting_channels"][i] == channel_id and json_data["twitter_user_ids"][i] == twitter_id:
        # 登録済み処理
        # リストから削除
        del json_data["setting_channels"][i]
        del json_data["twitter_user_ids"][i]
        # json書き込み
        json_make.edit_setting_json(guild_id, json_data["cool_down_time"],json_data["setting_channels"], json_data["twitter_user_ids"])
        await messege_send(interaction,'削除完了')
        return
  await messege_send(interaction,'削除するものがありません')

@tasks.loop(seconds=check_time)
async def loop():
  global old_time
  now_time = time.time()
  guild_ids = json_make.get_guild_id()
  for guild_id in guild_ids:
    json_data = await json_make.load_setting_json(guild_id)
    if json_data is None:
      # 読み込み失敗
      print('読み込み失敗')
      return
    if json_data["cool_down_time"] >= now_time - old_time:
      # 設定時間に達していない
      return

    old_time = time.time()
    for channel_id in json_data["setting_channels"]:
      #送信先チャンネル指定
      channel = duscord_client.get_channel(int(channel_id))
      # ツイート取得
      tweet_id,next_tweet_id = await twitter_client.Twikit_Msg(CHANMEL_NAME)
      # 同じ場合スキップ
      if(tweet_id == old_Msg1_id):
        return
      # 削除された時の対策用
      elif(tweet_id == old_Msg2_id):
        return
      # メッセージを更新
      old_Msg1_id = tweet_id
      old_Msg2_id = next_tweet_id
      # メッセージを送信
      url = f'https://fxtwitter.com/{CHANMEL_NAME}/status/{tweet_id}'
      print(url)
      await channel.send(url, silent=True)

duscord_client.run(TOKEN)