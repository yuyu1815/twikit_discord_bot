import json,os

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
import json

def edit_setting_json(guild_id, channel_id, cool_down_time, setting_channels, twitter_user_ids):
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

