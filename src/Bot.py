
import discord,os,time,re
#discord
from discord import app_commands
from discord.ext import tasks

from dotenv import load_dotenv
#local
import twitter_get,json_make
load_dotenv()
TOKEN = os.getenv('TOKEN')
Application_ID = os.getenv('Application_ID')
# 言語設定
languages = json_make.get_lang_json(os.getenv('Languages'))
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
#------------------ 以下コマンド類 ------------------
# channelとtwitter_id設定
@tree.command(name='set_twitter', description=languages["command_set_twitter"])
async def set_command(interaction: discord.Interaction,twitter_user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  #guild_id取得
  guild_id = interaction.guild_id
  #2重登録防ぎ
  json_data = json_make.load_setting_json(guild_id)
  if (json_data["setting_bool"][0] == False):
    await message_send(interaction, languages["setting_flag_msg"], True)
    return
  elif not await twitter_client.user_exist(twitter_user_name):
    await message_send(interaction, languages["unknown_user_msg"], True)
    return
  elif json_data is None:
    # まだ設定されていない場合
    json_make.edit_setting_json(guild_id, 1, [channel_id], [twitter_user_name],[True,True])
    json_data = json_make.load_setting_json(guild_id)
    # 表示する設定にしていない場合

  for i in range(len(json_data["setting_channels"])):
    if json_data["setting_channels"][i] == channel_id and json_data["twitter_user_names"][i] == twitter_user_name:
      # 登録済み処理
      await message_send(interaction, languages["duplicated_user_msg"],True)
      return
      # 登録完了
  json_data["setting_channels"].append(channel_id)
  json_data["twitter_user_names"].append(twitter_user_name)

  json_make.json_load_and_settings(guild_id, "setting_channels", json_data["setting_channels"])
  json_make.json_load_and_settings(guild_id, "twitter_user_names", json_data["twitter_user_names"])
  await message_send(interaction, languages["setting_completed_msg"], True)

# channelとtwitter_id削除
@tree.command(name='del_twitter', description=languages["command_del_twitter"])
async def del_command(interaction: discord.Interaction,user_name:str):
  #チャンネルid取得
  channel_id = interaction.channel_id
  guild_id = interaction.guild_id

  json_data = json_make.load_setting_json(guild_id)

  if json_data is None:
    # 読み込み失敗
    await message_send(interaction, languages["loading_failed_msg"],True)
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
      await message_send(interaction, languages["setting_completed_msg"],True)
      return
  # 登録されていない場合
  await message_send(interaction, languages["no_user_registration_msg"],True)
# クールダウンの設定
@tree.command(name='check-time', description=languages["command_check_time"])
async def cool_down(interaction: discord.Interaction,minutes:int):
  # 1分未満は1分に設定
  minutes = max(1,minutes)
  json_make.json_load_and_settings(interaction.guild_id, "cool_down_time", minutes)
  await message_send(interaction, languages["setting_completed_msg"],True)

@tree.command(name='change-setting-twitter-get', description=languages["command_change_setting_twitter_get"])
async def change_setting_twitter_get(interaction: discord.Interaction, mode: bool):
  # ギルドid
  guild_id = interaction.guild_id
  # ギルドidから現在の設定を読み込み
  json_data = json_make.load_setting_json(guild_id)
  if json_data is None:
    await message_send(interaction, languages["loading_failed_msg"],True)
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
      await message_send(interaction, languages["loading_failed_msg"], True)
      return
    # 現在の設定を切り替える
    json_data["setting_bool"][1] = mode
    # json書き込み
    json_make.json_load_and_settings(guild_id, "setting_bool", json_data["setting_bool"])
  await message_send(interaction, languages["setting_completed_msg"],True)
@tree.command(name='check-settings', description=languages["command_check_settings"])
async def check_setting(interaction: discord.Interaction):
  # ギルドid
  guild_id = interaction.guild_id
  # ギルドidからチャンネル、クールダウン、チャンネル、ツイッターidを取得
  json_data = json_make.load_setting_json(guild_id)
  if json_data is None:
    await message_send(interaction, languages["loading_failed_msg"],True)
    return
  setting_channels = json_data["setting_channels"]
  twitter_user_names = json_data["twitter_user_names"]
  cool_down_time = json_data["cool_down_time"]
  # 送信部分
  embed = discord.Embed(title=languages["embed_setting"], description=f"{languages['embed_check_time']} : {cool_down_time}{languages['embed_minutes']}\n{languages['embed_new_tweet']} : {json_data['setting_bool'][0]}\n{languages['embed_change_fxtwitter']}：{json_data['setting_bool'][1]}", color=0x219900)
  channel_string = ""
  twitter_user_names_string = ""
  message_count = 0
  message_flag = False
  for setting_channel,twitter_user_name in zip(setting_channels,twitter_user_names):
    message_count += 4 + len(str(setting_channel)) + 18 + len(twitter_user_name)
    # 4文字(チャンネル名) + 18文字(ツイッター名)
    # 1024文字に達したら送信
    if message_count >= 1024:
      embed.add_field(name=languages["embed_setting_channel"], value=channel_string, inline=True)
      embed.add_field(name=languages["embed_setting_user"], value=twitter_user_names_string, inline=True)
      if message_flag:
        await interaction.followup.send(embed=embed)
      else:
        await interaction.response.send_message(embed=embed)
      # 初期化
      embed = discord.Embed(title=languages["embed_setting_channel"], color=0x219900)
      message_count = 0
      channel_string = ""
      twitter_user_names_string = ""
      message_flag = True

    channel_string += f"<#{setting_channel}>\n"
    twitter_user_names_string += f"[{twitter_user_name}](https://x.com/{twitter_user_name})\n"


  embed.add_field(name=languages["embed_setting_channel"], value=channel_string, inline=True)
  embed.add_field(name=languages["embed_setting_user"], value=twitter_user_names_string, inline=True)
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
      print('Loading failed')
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
        print('Failed to get tweets')
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
