import json,os
# cookieを編集してTwikitを用に変換し保存
def Twitter_New_Json_edit():
    try:
        with open('./json/cookie.json', 'r') as file:
            data = json.load(file)
    except:
        os._exit(1)
        return

    result = {}
    for item in data:
        name = item.get("name")
        value = item.get("value")
        if name and value:
            result[name] = value

    with open('./json/cookie_edit.json', 'w') as file:
        json.dump(result, file, indent=4)

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
def edit_setting_json(guild_id, cool_down_time, setting_channels, twitter_user_ids):
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
        "twitter_user_ids": twitter_user_ids
    }

    # JSONファイルに保存
    with open('./json/DiscordSetting.json', 'w') as file:
        json.dump(data, file, indent=4)

def json_Load_And_Settings(guild_id,flag_setting_name,flag_string):
    cool_down_time, setting_channels, twitter_user_ids = load_setting_json(guild_id)
    edit_setting_json(guild_id,
                      flag_setting_name == "cool_down_time" ? flag_string : cool_down_time,
                      flag_setting_name == "setting_channels" ? flag_string : setting_channels,
                      flag_setting_name == "twitter_user_ids" ? flag_string : twitter_user_ids
    )

# ギルドid取得
def get_guild_id():
    try:
        with open('./json/DiscordSetting.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return list(data.keys())
# twiiterのメッセージを保存
def twitter_msg_edit( channel_Id, twitter_Id , msg1 , msg2):
    try:
        with open('./json/Twitter_msg.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data[str(channel_Id)][str(twitter_Id)][0] = msg1
    data[str(channel_Id)][str(twitter_Id)][1] = msg2

    # JSONファイルに保存
    with open('./json/Twitter_msg.json', 'w') as file:
        json.dump(data, file, indent=4)
# twitterのメッセージの取得
def load_Twitter_Msg(channel_id,twitter_Id):
    try:
        with open('./json/Twitter_msg.json', 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None,None
    return data[str(channel_id)][str(twitter_Id)]