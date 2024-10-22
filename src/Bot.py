
from turtledemo.penrose import start
import discord,os,time,re
#discord
from discord import app_commands
from discord.ext import tasks, commands

from dotenv import load_dotenv
#local
import twitter_get,json_make,scraping.aliexpress

from urllib.parse import urlparse, urlunparse
import json
load_dotenv()
TOKEN = os.getenv('TOKEN')
Application_ID = os.getenv('Application_ID')
Languages = os.getenv('Languages')
# 言語設定
#languages = json.load(f"./lang/{Languages}.json")
# いつもの呪文
intents = discord.Intents.all()
discord_client = discord.Client(intents=intents)

tree = app_commands.CommandTree(discord_client)
twitter_client = twitter_get.TwitterClient()
#aliexpress = scraping.aliexpress.aliexpress()
old_time = time.time()

@discord_client.event
async def on_ready():
  print('Login OK')
  if Application_ID is not None:
    print(f"setting URL:https://discord.com/developers/applications/{Application_ID}/installation")
    # 権限を指定して招待URLを生成
    print(f'Invite URL: https://discord.com/oauth2/authorize?client_id={Application_ID}')
  await tree.sync()
  # twitterログイン
  await twitter_client.load_client()
  loop.start()

#discordとコンソールに送信
async def message_send(interaction, msg,ephemeral=False):
  print(msg)
  await interaction.response.send_message(msg, ephemeral=ephemeral)
  return
# https://qiita.com/hisuie08/items/5b63924156080694fc81
"""async def send_embed_aliexpress(url_pattern):
  title, img_url, price, price_original, price_off, count, postage, skip_time, choice, star, review = aliexpress.get_data(url_pattern)
  # 黄色と赤
  color = 0xffff00 if choice else 0xff0000
  parsed_url = urlparse(url_pattern)
  clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
  count_star = ''
  for i in range(int(star)):
    count_star += '★'
  for i in range(5 - int(star)):
    count_star += '☆'
  embed = discord.Embed(title=f"[{title}]({clean_url})", description=f"評価:{count_star} {star} {review}", color=color)
  if choice:
    embed.set_thumbnail(file="./png/choice.png")
  if price:
    embed.add_field(name='価格', value=f'通常価格:　~~{price_original}~~{price}\n**{price_off}**\n評価: {star} {review}', inline=False)
  else:
    embed.add_field(name='価格', value=f'現在価格: {price}', inline=False)
  embed.add_field(name='配送', value=f'送料: {postage}\n発送日時: {skip_time}', inline=False)
  embed.set_image(url=img_url)"""
#------------------ 以下コマンド類 ------------------
# channelとtwitter_id設定
@tree.command(name='set_twitter', description='コマンドを実行したチャンネルでtwitterを登録します')
async def set_command(interaction: discord.Interaction,twitter_user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  #guild_id取得
  guild_id = interaction.guild_id
  #2重登録防ぎ
  json_data = json_make.load_setting_json(guild_id)
  if (json_data["setting_bool"][0] == False):
    await message_send(interaction, '設定でOFFになっているため追加できませんでした', True)
    return
  elif not await twitter_client.user_exist(twitter_user_name):
    await message_send(interaction, 'User名が存在しないものか鍵のかかったアカウントです', True)
    return
  elif json_data is None:
    # まだ設定されていない場合
    json_make.edit_setting_json(guild_id, 1, [channel_id], [twitter_user_name],[True,True])
    json_data = json_make.load_setting_json(guild_id)
    # 表示する設定にしていない場合

  for i in range(len(json_data["setting_channels"])):
    if json_data["setting_channels"][i] == channel_id and json_data["twitter_user_names"][i] == twitter_user_name:
      # 登録済み処理
      await message_send(interaction, 'すでに設定しているため追加できませんでした',True)
      return
      # 登録完了
  json_data["setting_channels"].append(channel_id)
  json_data["twitter_user_names"].append(twitter_user_name)

  json_make.json_load_and_settings(guild_id, "setting_channels", json_data["setting_channels"])
  json_make.json_load_and_settings(guild_id, "twitter_user_names", json_data["twitter_user_names"])
  await message_send(interaction, '設定完了', True)

# channelとtwitter_id削除
@tree.command(name='del_twitter', description='コマンドを実行したチャンネルで登録していたものを削除します')
async def del_command(interaction: discord.Interaction,user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  guild_id = interaction.guild_id

  json_data = json_make.load_setting_json(guild_id)

  if json_data is None:
    # 読み込み失敗
    await message_send(interaction, '設定jsonを読み込むことができませんでした',True)
    return

  for i in range(len(json_data["setting_channels"])):
    if json_data["setting_channels"][i] == channel_id and json_data["twitter_user_names"][i] == user_name:
      # 登録済み処理
      # リストから削除
      del json_data["setting_channels"][i]
      del json_data["twitter_user_names"][i]
      # json書き込み
      json_make.del_twitter_msg(channel_id, user_name)
      json_make.json_load_and_settings(guild_id, "setting_channels", json_data["setting_channels"])
      json_make.json_load_and_settings(guild_id, "twitter_user_names", json_data["twitter_user_names"])
      await message_send(interaction, '削除完了',True)
      return
  # 登録されていない場合
  await message_send(interaction, '設定されていないため削除できませんでした',True)
# クールダウンの設定
@tree.command(name='check-time', description='twitterをチェックする間隔(分)を設定(小数点以下は使えません)')
async def cool_down(interaction: discord.Interaction,minutes:int):
  # 1分未満は1分に設定
  if minutes <= 1:
    minutes = 1
  json_make.json_load_and_settings(interaction.guild_id, "cool_down_time", minutes)
  await message_send(interaction, '設定完了',True)

@tree.command(name='change-setting-twitter-get', description='ツイッターの自動更新の取得設定(True/False)')
async def change_setting_twitter_get(interaction: discord.Interaction, mode: bool):
  # ギルドid
  guild_id = interaction.guild_id
  # ギルドidから現在の設定を読み込み
  json_data = json_make.load_setting_json(guild_id)
  if json_data is None:
    await message_send(interaction, '設定jsonを読み込むことができませんでした',True)
    return
  # 現在の設定を切り替える
  json_data["setting_bool"][0] = mode
  # json書き込み
  json_make.json_load_and_settings(guild_id, "setting_bool", json_data["setting_bool"])

  @tree.command(name='change-setting-url-preview', description='urlを見てる形にしてくれます(True/False)')
  async def change_setting(interaction: discord.Interaction, mode: bool):
    # ギルドid
    guild_id = interaction.guild_id
    # ギルドidから現在の設定を読み込み
    json_data = json_make.load_setting_json(guild_id)
    if json_data is None:
      await message_send(interaction, '設定jsonを読み込むことができませんでした', True)
      return
    # 現在の設定を切り替える
    json_data["setting_bool"][1] = mode
    # json書き込み
    json_make.json_load_and_settings(guild_id, "setting_bool", json_data["setting_bool"])
  await message_send(interaction, '設定完了',True)
@tree.command(name='check-setting', description='現在の設定しているチャンネルなどを表示')
async def check_setting(interaction: discord.Interaction):
  # ギルドid
  guild_id = interaction.guild_id
  # ギルドidからチャンネル、クールダウン、チャンネル、ツイッターidを取得
  json_data = json_make.load_setting_json(guild_id)
  if json_data is None:
    await message_send(interaction, '設定jsonを読み込むことができませんでした',True)
    return
  setting_channels = json_data["setting_channels"]
  twitter_user_names = json_data["twitter_user_names"]
  cool_down_time = json_data["cool_down_time"]
  # 送信部分
  embed = discord.Embed(title="設定中チャンネル", description=f"チェックする間隔{cool_down_time}分\ntweet更新：{json_data['setting_bool'][0]}\nfxtwitterに変換：{json_data['setting_bool'][1]}", color=0x219900)
  channel_string = ""
  twitter_user_names_string = ""
  message_count = 0
  message_flag = False
  for setting_channel,twitter_user_name in zip(setting_channels,twitter_user_names):
    message_count += 4 + len(str(setting_channel)) + 18 + len(twitter_user_name)
    # 4文字(チャンネル名) + 18文字(ツイッター名)
    # 1024文字に達したら送信
    if message_count >= 1024:
      embed.add_field(name="設定チャンネル", value=channel_string, inline=True)
      embed.add_field(name="設定ツイッター", value=twitter_user_names_string, inline=True)
      if message_flag:
        await interaction.followup.send(embed=embed)
      else:
        await interaction.response.send_message(embed=embed)
      # 初期化
      embed = discord.Embed(title="設定中チャンネル", color=0x219900)
      message_count = 0
      channel_string = ""
      twitter_user_names_string = ""
      message_flag = True

    channel_string += f"<#{setting_channel}>\n"
    twitter_user_names_string += f"[{twitter_user_name}](https://x.com/{twitter_user_name})\n"


  embed.add_field(name="設定チャンネル", value=channel_string, inline=True)
  embed.add_field(name="設定ツイッター", value=twitter_user_names_string, inline=True)
  if message_flag:
    await interaction.followup.send(embed=embed)
  else:
    await interaction.response.send_message(embed=embed)
# x.comの置き換え
@discord_client.event
async def on_message(message):
  #bot無視
  if message.author.bot:
    return
  print(f"{message.author.name}: {message.content}")
  json_data = json_make.load_setting_json(message.guild.id)

  replace_url = ['https://x.com', 'https://twitter.com', 'https://www.tiktok.com', 'https://tiktok.com']
  after_replace_url = [f"https://fxtwitter.com", "https://fxtwitter.com", "https://fxtiktok.com", "https://fxtiktok.com"]
  if json_data is None and json_data["setting_bool"][0] is False:
    return


  #if "aliexpress.com/item/" in url_pattern:
  #  await send_embed_aliexpress(updated_content)
  # アリエクを投稿された場合

  # twitter.comまたはx.comが投稿されたことを確認する。
  # tiktok版も見つけたので置き換え
  url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
  re_updated_content = ''
  updated_content = re.findall(url_pattern, message.content)[0]
  for after,before in zip(after_replace_url,replace_url):
    if before in updated_content:
      re_updated_content = updated_content.replace(before, after)
      await message.edit(suppress=True)
      await message.channel.send(f"[￶]({re_updated_content})")
      break
  #ツイートに含まれるほかのurlも表示
  if 'https://fxtwitter.com' in re_updated_content:
      print(updated_content)
      other_url = await twitter_client.twitter_msg_get_url(updated_content)
      if other_url is None:
        return
      for i in other_url:
          if "https://fxtwitter.com" in i:
            await message.channel.send(f"[￶]({i})")
          else:
            await message.channel.send(i)

@tasks.loop(seconds=10)
async def loop():
  global old_time
  # 現在の秒数を取得
  now_time = time.time()
  # ギルドidを取得
  guild_ids = json_make.get_guild_id()
  if guild_ids is None:
    return
  for guild_id in guild_ids:
    # ギルドidからチャンネル、クールダウン、チャンネル、ツイッターidを取得
    json_data = json_make.load_setting_json(guild_id)
    if json_data is None and json_data["setting_bool"][1] is False:
      # 読み込み失敗
      print('読み込み失敗')
      continue
    #cool_down_time は分単位
    if int(json_data["cool_down_time"])*60 >= now_time - old_time:
      # 設定時間に達していない
      continue
    # 時間リセット
    old_time = time.time()
    for channel_id,twitter_user_name in zip(json_data["setting_channels"],json_data["twitter_user_names"]):
      #送信先チャンネル指定
      channel = discord_client.get_channel(channel_id)
      # ツイート取得
      tweet_id,next_tweet_id = await twitter_client.twikit_msg(twitter_user_name)
      if tweet_id is None:
        # ツイート取得失敗
        print('ツイート取得失敗')
        continue
      old_msg_id = json_make.load_twitter_msg(channel_id, twitter_user_name)
      # 未設定の場合は初期化
      old_msg_id = [
        old_msg_id[0] if old_msg_id[0] is not None else 0,
        old_msg_id[1] if old_msg_id[1] is not None else 0
      ]
      # 同じ場合スキップ 削除された時の対策用
      if tweet_id == old_msg_id[0] or tweet_id == old_msg_id[1]:
        continue
      # リツイートの場合スキップ
      if await twitter_client.get_retweet(tweet_id):
        continue
      # メッセージを更新
      old_msg_id = [tweet_id,next_tweet_id]
      json_make.twitter_msg_edit(channel_id,twitter_user_name,old_msg_id)
      # メッセージを送信
      url = f'https://fxtwitter.com/{twitter_user_name}/status/{tweet_id}'
      print(url)
      await channel.send(url, silent=True)
      # リツイートがあった場合はそれも表示

discord_client.run(TOKEN)