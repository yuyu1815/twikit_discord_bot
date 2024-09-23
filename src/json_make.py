import json
import sys
# cookieを編集してTwikitを用に変換し保存
def twitter_new_json_edit():
    try:
        with open('./json/cookie.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        sys.exit()

    result = {}
    for item in data:
        name = item.get("name")
        value = item.get("value")
        if name and value:
            result[name] = value

    with open('./json/cookie_edit.json', 'w') as file:
        json.dump(result, file, sort_keys=True, indent=4)

# ギルドidから設定チャンネルを取得
def load_setting_json(guild_id):
    try:
        with open('./json/DiscordSetting.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if str(guild_id) in data:
        return data[str(guild_id)]
    else:
        return None

# 以下の設定を保存 ギルドid,ギルドごとのチェック用クールダウン,チャンネル(配列),ツイッターid(配列)
def edit_setting_json(guild_id, cool_down_time, setting_channels, twitter_user_names):
    try:
        # guildごとのjsonファイルの読み込み
        with open('./json/DiscordSetting.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # ファイルが存在しないか、読み込めない場合は新規作成
        data = {}

    # guild_idが存在する場合は編集、存在しない場合は追加
    data[str(guild_id)] = {
        "cool_down_time": cool_down_time,
        "setting_channels": setting_channels,
        "twitter_user_names": twitter_user_names
    }

    # JSONファイルに保存
    with open('./json/DiscordSetting.json', 'w') as file:
        json.dump(data, file, sort_keys=True, indent=4)

def json_load_and_settings(guild_id, flag_setting_name, flag_string):
    json_data = load_setting_json(guild_id)
    edit_setting_json(guild_id,
                      flag_string if flag_setting_name == "cool_down_time" else json_data["cool_down_time"],
                      flag_string if flag_setting_name == "setting_channels" else json_data["setting_channels"],
                      flag_string if flag_setting_name == "twitter_user_names" else json_data["twitter_user_names"]
                      )
# ギルドid取得
def get_guild_id():
    try:
        with open('./json/DiscordSetting.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return list(data.keys())
# twitterのメッセージを保存
def twitter_msg_edit(channel_id, twitter_id, msg):
    try:
        with open('./json/Twitter_msg.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    # チャンネルIDが存在しない場合は初期化
    if str(channel_id) not in data:
        data[str(channel_id)] = {}

    # Twitter IDを設定
    data[str(channel_id)][str(twitter_id)] = msg

    # JSONファイルに保存
    with open('./json/Twitter_msg.json', 'w') as file:
        json.dump(data, file, sort_keys=True, indent=4)
# twitterのメッセージの取得
def load_twitter_msg(channel_id, twitter_id):
    try:
        with open('./json/Twitter_msg.json', 'r') as file:
            data = json.load(file)
        return data[str(channel_id)][str(twitter_id)]
    except:
        return None,None

