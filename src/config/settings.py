import json
import os
import sys
from pathlib import Path

class Settings:
    """
    Settings class for managing all file I/O operations including settings, language files, and data.
    This class replaces the functionality in the old json_make.py file.

    Note: The JSON-based methods for guild configuration and Twitter messages are deprecated
    and will be removed in a future version. Use the Database class instead.

    設定、言語ファイル、データを含むすべてのファイルI/O操作を管理するための設定クラスです。
    このクラスは、古いjson_make.pyファイルの機能を置き換えるものです。

    注：ギルド設定およびTwitterメッセージのJSONベースのメソッドは非推奨であり、
    将来のバージョンで削除されます。代わりにDatabaseクラスを使用してください。
    """

    def __init__(self, language='en_US'):
        """
        Initialize the Settings class with the specified language.
        It sets up paths for project root, data directory, and language files.

        Args:
            language (str): The language code to use (default: 'en_US').

        指定された言語でSettingsクラスを初期化します。
        プロジェクトルート、データディレクトリ、言語ファイルのパスを設定します。

        Args:
            language (str): 使用する言語コード（デフォルト: 'en_US'）。
        """
        self.language = language
        # Define the project root directory.
        # プロジェクトのルートディレクトリを定義します。
        self.project_root = Path(__file__).parent.parent.parent
        # Define the data directory path.
        # データディレクトリのパスを定義します。
        self.data_dir = self.project_root / 'data'
        # Define the language files directory path.
        # 言語ファイルのディレクトリパスを定義します。
        self.lang_dir = self.project_root / 'src' / 'lang'

        # Load language data from the specified language file.
        # 指定された言語ファイルから言語データをロードします。
        self.lang_data = self.get_lang_json(language)

    def get_lang_json(self, lang):
        """
        Load a language file from the language directory.

        Args:
            lang (str): The language code (e.g., 'en_US', 'ja_JP').

        Returns:
            dict: A dictionary containing the language-specific strings.

        Raises:
            SystemExit: If the language file cannot be found or parsed.

        言語ディレクトリから言語ファイルをロードします。

        Args:
            lang (str): 言語コード（例: 'en_US'、'ja_JP'）。

        Returns:
            dict: 言語固有の文字列を含む辞書。

        Raises:
            SystemExit: 言語ファイルが見つからないか、解析できない場合。
        """
        try:
            with open(self.lang_dir / f'{lang}.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
        except IOError:
            print(f'Error: Could not find language file {lang}.json')
            sys.exit() # Exit the application if a critical language file is missing.
        return data

    def twitter_new_json_edit(self):
        """
        Reads the original 'cookie.json' file and converts its format
        to 'cookie_edit.json', which is compatible with the Twikit library.

        Reads the original 'cookie.json' file and converts its format
        to 'cookie_edit.json', which is compatible with the Twikit library.

        元の 'cookie.json' ファイルを読み込み、その形式をTwikitライブラリと互換性のある
        'cookie_edit.json' に変換します。
        """
        try:
            with open(self.data_dir / 'cookie.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Could not find or parse cookie.json")
            sys.exit() # Exit if the cookie file is critical and cannot be processed.

        result = {}
        for item in data:
            name = item.get("name")
            value = item.get("value")
            if name and value:
                result[name] = value

        with open(self.data_dir / 'cookie_edit.json', 'w') as file:
            json.dump(result, file, sort_keys=True, indent=4)

    def get_guild_config(self, guild_id):
        """
        Get the configuration for a specific guild from the deprecated DiscordSetting.json file.

        Deprecated: Use Database.get_guild_settings() instead.

        Args:
            guild_id: The ID of the guild.

        Returns:
            dict: The guild configuration as a dictionary, or None if not found or file error.

        非推奨のDiscordSetting.jsonファイルから特定のギルドの設定を取得します。

        非推奨：代わりにDatabase.get_guild_settings()を使用してください。

        Args:
            guild_id: ギルドのID。

        Returns:
            dict: 辞書形式のギルド設定、または見つからない場合やファイルエラーの場合はNone。
        """
        try:
            with open(self.data_dir / 'DiscordSetting.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

        if str(guild_id) in data:
            return data[str(guild_id)]
        else:
            return None

    def update_guild_config(self, guild_id, cool_down_time=None, setting_channels=None, 
                           twitter_user_names=None, setting_bool=None, last_checked_time=None):
        """
        Update the configuration for a specific guild in the deprecated DiscordSetting.json file.

        Deprecated: Use Database.update_guild_settings() instead.

        Args:
            guild_id: The ID of the guild.
            cool_down_time (int, optional): The cool down time in minutes.
            setting_channels (list, optional): List of channel IDs.
            twitter_user_names (list, optional): List of Twitter user names.
            setting_bool (list, optional): List of boolean settings.
            last_checked_time (int, optional): The last time tweets were checked (Unix timestamp).

        非推奨のDiscordSetting.jsonファイルで特定のギルドの設定を更新します。

        非推奨：代わりにDatabase.update_guild_settings()を使用してください。

        Args:
            guild_id: ギルドのID。
            cool_down_time (int, optional): クールダウン時間（分）。
            setting_channels (list, optional): チャンネルIDのリスト。
            twitter_user_names (list, optional): Twitterユーザー名のリスト。
            setting_bool (list, optional): ブール設定のリスト。
            last_checked_time (int, optional): 最後にツイートがチェックされた時刻（Unixタイムスタンプ）。
        """
        try:
            # Load existing guild settings from the JSON file.
            # JSONファイルから既存のギルド設定をロードします。
            with open(self.data_dir / 'DiscordSetting.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is invalid, initialize with an empty dictionary.
            # ファイルが存在しないか無効な場合、空の辞書で初期化します。
            data = {}

        # Get current settings for the guild or create new ones with default values.
        # ギルドの現在の設定を取得するか、デフォルト値で新しい設定を作成します。
        if str(guild_id) in data:
            guild_data = data[str(guild_id)]
        else:
            guild_data = {
                "cool_down_time": 1,
                "setting_bool": [True, True],
                "setting_channels": [],
                "twitter_user_names": [],
                "last_checked_time": 0
            }

        # Update settings if new values are provided.
        # 新しい値が提供された場合、設定を更新します。
        if cool_down_time is not None:
            guild_data["cool_down_time"] = cool_down_time
        if setting_channels is not None:
            guild_data["setting_channels"] = setting_channels
        if twitter_user_names is not None:
            guild_data["twitter_user_names"] = twitter_user_names
        if setting_bool is not None:
            guild_data["setting_bool"] = setting_bool
        if last_checked_time is not None:
            guild_data["last_checked_time"] = last_checked_time

        # Save the updated settings back to the JSON file.
        # 更新された設定をJSONファイルに保存します。
        data[str(guild_id)] = guild_data
        with open(self.data_dir / 'DiscordSetting.json', 'w') as file:
            json.dump(data, file, sort_keys=True, indent=4)

    def get_all_guild_ids(self):
        """
        Get all guild IDs from the deprecated DiscordSetting.json file.

        Deprecated: Use Database.get_all_guild_ids() instead.

        Returns:
            list: A list of string guild IDs, or None if the file doesn't exist or is invalid.

        非推奨のDiscordSetting.jsonファイルからすべてのギルドIDを取得します。

        非推奨：代わりにDatabase.get_all_guild_ids()を使用してください。

        Returns:
            list: 文字列形式のギルドIDのリスト、またはファイルが存在しないか無効な場合はNone。
        """
        try:
            with open(self.data_dir / 'DiscordSetting.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        return list(data.keys())

    def get_twitter_msg(self, channel_id, twitter_id):
        """
        Get the Twitter message (last two tweet IDs) for a specific channel and Twitter ID
        from the deprecated Twitter_msg.json file.

        Deprecated: Use Database.get_tweet_history() instead.

        Args:
            channel_id: The ID of the channel.
            twitter_id: The Twitter ID (username or user ID).

        Returns:
            list: A list containing the last two tweet IDs, or [None, None] if not found or file error.

        非推奨のTwitter_msg.jsonファイルから、特定のチャンネルとTwitter IDのTwitterメッセージ（最新2つのツイートID）を取得します。

        非推奨：代わりにDatabase.get_tweet_history()を使用してください。

        Args:
            channel_id: チャンネルのID。
            twitter_id: Twitter ID（ユーザー名またはユーザーID）。

        Returns:
            list: 最新2つのツイートIDを含むリスト、または見つからない場合やファイルエラーの場合は[None, None]。
        """
        try:
            with open(self.data_dir / 'Twitter_msg.json', 'r') as file:
                data = json.load(file)
            return data[str(channel_id)][str(twitter_id)]
        except:
            return None, None

    def update_twitter_msg(self, channel_id, twitter_id, msg):
        """
        Update the Twitter message (last two tweet IDs) for a specific channel and Twitter ID
        in the deprecated Twitter_msg.json file.

        Deprecated: Use Database.update_tweet_history() instead.

        Args:
            channel_id: The ID of the channel.
            twitter_id: The Twitter ID (username or user ID).
            msg: The message (list of tweet IDs) to save.

        非推奨のTwitter_msg.jsonファイルで、特定のチャンネルとTwitter IDのTwitterメッセージ（最新2つのツイートID）を更新します。

        非推奨：代わりにDatabase.update_tweet_history()を使用してください。

        Args:
            channel_id: チャンネルのID。
            twitter_id: Twitter ID（ユーザー名またはユーザーID）。
            msg: 保存するメッセージ（ツイートIDのリスト）。
        """
        try:
            with open(self.data_dir / 'Twitter_msg.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {} # Initialize with empty dictionary if file not found or invalid.

        # Initialize channel entry if it doesn't exist.
        # チャンネルエントリが存在しない場合、初期化します。
        if str(channel_id) not in data:
            data[str(channel_id)] = {}

        # Save the message (tweet IDs).
        # メッセージ（ツイートID）を保存します。
        data[str(channel_id)][str(twitter_id)] = msg

        with open(self.data_dir / 'Twitter_msg.json', 'w') as file:
            json.dump(data, file, sort_keys=True, indent=4)

    def delete_twitter_msg(self, channel_id, twitter_id):
        """
        Delete the Twitter message for a specific channel and Twitter ID
        from the deprecated Twitter_msg.json file.

        Deprecated: Use Database.remove_twitter_feed() instead.

        Args:
            channel_id: The ID of the channel.
            twitter_id: The Twitter ID (username or user ID).

        非推奨のTwitter_msg.jsonファイルから、特定のチャンネルとTwitter IDのTwitterメッセージを削除します。

        非推奨：代わりにDatabase.remove_twitter_feed()を使用してください。

        Args:
            channel_id: チャンネルのID。
            twitter_id: Twitter ID（ユーザー名またはユーザーID）。
        """
        try:
            with open(self.data_dir / 'Twitter_msg.json', 'r') as file:
                data = json.load(file)
            # Delete the specific Twitter message entry.
            # 特定のTwitterメッセージエントリを削除します。
            del data[str(channel_id)][str(twitter_id)]
            with open(self.data_dir / 'Twitter_msg.json', 'w') as file:
                json.dump(data, file, sort_keys=True, indent=4)
        except:
            # Ignore errors if the entry or file doesn't exist.
            # エントリまたはファイルが存在しない場合のエラーは無視します。
            pass