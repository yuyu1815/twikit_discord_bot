import discord,os,time
from discord import app_commands
from dotenv import load_dotenv
import twitter_get,json_make
from discord.ext import tasks

load_dotenv()
TOKEN = os.getenv('TOKEN')

# いつもの呪文
intents = discord.Intents.default()
duscord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(duscord_client)

twitter_client = twitter_get.Twitter_Client()

old_time = time.time()

@duscord_client.event
async def on_ready():
  print('Login OK')
  await tree.sync()
  # twitterログイン
  await twitter_client.load_client()
  loop.start()

#discordとコンソールに送信
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

  for i in range(len(json_data["setting_channels"])):
    if json_data["setting_channels"][i] == channel_id and json_data["twitter_user_ids"][i] == twitter_id:
      # 登録済み処理
      # リストから削除
      del json_data["setting_channels"][i]
      del json_data["twitter_user_ids"][i]
      # json書き込み
      json_make.json_Load_And_Settings(guild_id,"setting_channels",json_data["setting_channels"])
      json_make.json_Load_And_Settings(guild_id,"twitter_user_ids",json_data["twitter_user_ids"])
      await messege_send(interaction,'削除完了')
      return

  await messege_send(interaction,'削除するものがありません')
# クールダウンの設定
@tree.command(name='check-time', description='twitterをチェックする間隔(分)を設定(小数点以下は使えません)')
async def cool_down(interaction: discord.Interaction,minutes:int):
  # 1分未満は1分に設定
  if(minutes <= 1):
    minutes = 1
  json_make.json_Load_And_Settings(guild_id, "cool_down_time", minutes)

@tree.command(name='check-setting', description='現在の設定しているチャンネルなどを表示')
async def check_setting(interaction: discord.Interaction):
  # ギルドid
  guild_id = interaction.guild_id
  # ギルドidからチャンネル、クールダウン、チャンネル、ツイッターidを取得
  json_data = json_make.load_setting_json(guild_id)
  settin_channels = json_data["setting_channels"]
  twitter_user_ids = json_data["twitter_user_ids"]
  cool_down_time = json_data["cool_down_time"]
  if json_data is None:
  else:
  # 送信部分


@tasks.loop(seconds=1)
async def loop():
  global old_time
  # 現在の秒数を取得
  now_time = time.time()
  # ギルドidを取得
  guild_ids = json_make.get_guild_id()
  if(guild_ids is None):
    return
  for guild_id in guild_ids:
    # ギルドidからチャンネル、クールダウン、チャンネル、ツイッターidを取得
    json_data = json_make.load_setting_json(guild_id)
    if json_data is None:
      # 読み込み失敗
      print('読み込み失敗')
      #コンティニュー
    #cool_down_time は分単位
    if int(json_data["cool_down_time"])*60 >= now_time - old_time:
      # 設定時間に達していない
      #コンティニュー
    # 時間リセットs
    old_time = time.time()
    for channel_id,twitter_user_id  in zip(json_data["setting_channels"],json_data["twitter_user_ids"]):
      #送信先チャンネル指定
      channel = duscord_client.get_channel(channel_id)
      # Twitteridから名前に変換
      twitter_name =
      # ツイート取得
      tweet_id,next_tweet_id = await twitter_client.Twikit_Msg(twitter_name)
      old_Msg_id = json_make.load_Twitter_Msg(channel_id,twitter_user_id)
      # 未設定の場合は初期化
      old_Msg_id = [
        old_Msg_id[0] if old_Msg_id[0] is not None else 0,
        old_Msg_id[1] if old_Msg_id[1] is not None else 0
      ]
      # 同じ場合スキップ
      if(tweet_id == old_Msg_id[0]):
        #コンティニュー
      # 削除された時の対策用
      elif(tweet_id == old_Msg_id[1]):
        #コンティニュー
      # メッセージを更新
      old_Msg_id = [tweet_id,next_tweet_id]
      json_make.twitter_msg_edit(old_Msg1_id[0],old_Msg1_id[1])
      # メッセージを送信
      url = f'https://fxtwitter.com/{twitter_name}/status/{tweet_id}'
      print(url)
      await channel.send(url, silent=True)

duscord_client.run(TOKEN)