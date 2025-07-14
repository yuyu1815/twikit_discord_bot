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
    """

    def __init__(self, language='en_US'):
        """
        Initialize the Settings class with the specified language.

        Args:
            language (str): The language code to use (default: 'en_US')
        """
        self.language = language
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / 'data'
        self.lang_dir = self.project_root / 'src' / 'lang'

        # Load language file
        self.lang_data = self.get_lang_json(language)

    def get_lang_json(self, lang):
        """
        Load a language file.

        Args:
            lang (str): The language code

        Returns:
            dict: The language data
        """
        try:
            with open(self.lang_dir / f'{lang}.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
        except IOError:
            print(f'Error: Could not find language file {lang}.json')
            sys.exit()
        return data

    def twitter_new_json_edit(self):
        """
        Edit the cookie.json file to make it compatible with Twikit.
        """
        try:
            with open(self.data_dir / 'cookie.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Could not find or parse cookie.json")
            sys.exit()

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
        Get the configuration for a specific guild.

        Deprecated: Use Database.get_guild_settings() instead.

        Args:
            guild_id: The ID of the guild

        Returns:
            dict: The guild configuration or None if not found
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
        Update the configuration for a specific guild.

        Deprecated: Use Database.update_guild_settings() instead.

        Args:
            guild_id: The ID of the guild
            cool_down_time (int, optional): The cool down time in minutes
            setting_channels (list, optional): List of channel IDs
            twitter_user_names (list, optional): List of Twitter user names
            setting_bool (list, optional): List of boolean settings
            last_checked_time (int, optional): The last time tweets were checked
        """
        try:
            # Load existing guild settings
            with open(self.data_dir / 'DiscordSetting.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is invalid, create a new one
            data = {}

        # Get current settings or create new ones
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

        # Update settings if provided
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

        # Save updated settings
        data[str(guild_id)] = guild_data
        with open(self.data_dir / 'DiscordSetting.json', 'w') as file:
            json.dump(data, file, sort_keys=True, indent=4)

    def get_all_guild_ids(self):
        """
        Get all guild IDs from the settings file.

        Deprecated: Use Database.get_all_guild_ids() instead.

        Returns:
            list: List of guild IDs or None if the file doesn't exist
        """
        try:
            with open(self.data_dir / 'DiscordSetting.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        return list(data.keys())

    def get_twitter_msg(self, channel_id, twitter_id):
        """
        Get the Twitter message for a specific channel and Twitter ID.

        Deprecated: Use Database.get_tweet_history() instead.

        Args:
            channel_id: The ID of the channel
            twitter_id: The Twitter ID

        Returns:
            list: The Twitter message or [None, None] if not found
        """
        try:
            with open(self.data_dir / 'Twitter_msg.json', 'r') as file:
                data = json.load(file)
            return data[str(channel_id)][str(twitter_id)]
        except:
            return None, None

    def update_twitter_msg(self, channel_id, twitter_id, msg):
        """
        Update the Twitter message for a specific channel and Twitter ID.

        Deprecated: Use Database.update_tweet_history() instead.

        Args:
            channel_id: The ID of the channel
            twitter_id: The Twitter ID
            msg: The message to save
        """
        try:
            with open(self.data_dir / 'Twitter_msg.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        # Initialize channel if it doesn't exist
        if str(channel_id) not in data:
            data[str(channel_id)] = {}

        # Save the message
        data[str(channel_id)][str(twitter_id)] = msg

        with open(self.data_dir / 'Twitter_msg.json', 'w') as file:
            json.dump(data, file, sort_keys=True, indent=4)

    def delete_twitter_msg(self, channel_id, twitter_id):
        """
        Delete the Twitter message for a specific channel and Twitter ID.

        Deprecated: Use Database.remove_twitter_feed() instead.

        Args:
            channel_id: The ID of the channel
            twitter_id: The Twitter ID
        """
        try:
            with open(self.data_dir / 'Twitter_msg.json', 'r') as file:
                data = json.load(file)
            del data[str(channel_id)][str(twitter_id)]
            with open(self.data_dir / 'Twitter_msg.json', 'w') as file:
                json.dump(data, file, sort_keys=True, indent=4)
        except:
            pass
