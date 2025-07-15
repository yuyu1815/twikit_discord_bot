import discord
import os
import time
from discord.ext import tasks, commands
from pathlib import Path
import importlib
import inspect

from src.core.twitter_client import TwitterClient
from src.config.settings import Settings
from src.core.database import Database

class MyBot(commands.Bot):
    """
    Custom Discord bot class that inherits from commands.Bot.
    This class encapsulates the core functionality of the bot.
    """

    def __init__(self, language='en_US'):
        """
        Initialize the bot with the specified language.

        Args:
            language (str): The language code to use (default: 'en_US')
        """
        # Set up intents
        intents = discord.Intents.all()

        # Load environment variables
        self.token = os.getenv('TOKEN')
        application_id = os.getenv('Application_ID')

        # Pass application_id to the parent class constructor
        super().__init__(command_prefix='!', intents=intents, application_id=application_id)

        # Initialize settings, database, and Twitter client
        self.settings = Settings(language)
        self.db = Database()
        self.twitter_client = TwitterClient(settings=self.settings)

        # Flag to track if migration has been performed
        self.migration_done = False

    async def setup_hook(self):
        """
        Set up the bot when it's starting.
        This method is called automatically by discord.py.
        """
        print(self.settings.lang_data["bot_setting_up"])

        # Load all cogs from the cogs directory
        await self.load_cogs()

        # Initialize the Twitter client
        await self.twitter_client.load_client()

        # Migrate data from JSON to database if needed
        await self.migrate_data_if_needed()

        # Start the background task
        self.check_twitter_updates.start()

    async def migrate_data_if_needed(self):
        """
        Migrate data from JSON files to the database if it hasn't been done yet.
        This is a one-time operation that happens at bot startup.
        After successful migration, the JSON files are renamed to prevent them from being read again.
        """
        data_dir = Path(self.settings.data_dir)
        discord_settings_file = data_dir / 'DiscordSetting.json'
        twitter_msg_file = data_dir / 'Twitter_msg.json'

        # If no JSON files exist, mark migration as complete and skip
        if not discord_settings_file.exists() and not twitter_msg_file.exists():
            self.db.set_migration_completed()
            self.migration_done = True
            # print(self.settings.lang_data["bot_migration_not_needed"])  # Optional: Add a new lang key for this
            return

        # Check if migration has already been completed
        if self.db.is_migration_completed():
            self.migration_done = True
            print(self.settings.lang_data["bot_migration_completed"])
            return

        print(self.settings.lang_data["bot_migration_starting"])

        # Perform the migration
        success = self.db.migrate_from_json(self.settings)

        if success:
            self.migration_done = True
            print(self.settings.lang_data["bot_migration_success"])

            # Rename JSON files to prevent them from being read again
            try:
                data_dir = Path(self.settings.data_dir)
                discord_settings_file = data_dir / 'DiscordSetting.json'
                twitter_msg_file = data_dir / 'Twitter_msg.json'

                if discord_settings_file.exists():
                    discord_settings_file.rename(data_dir / 'DiscordSetting.json.migrated')
                    print(self.settings.lang_data["bot_renamed_file"].format(discord_settings_file, f"{discord_settings_file}.migrated"))

                if twitter_msg_file.exists():
                    twitter_msg_file.rename(data_dir / 'Twitter_msg.json.migrated')
                    print(self.settings.lang_data["bot_renamed_file"].format(twitter_msg_file, f"{twitter_msg_file}.migrated"))
            except Exception as e:
                print(self.settings.lang_data["bot_rename_failed"].format(e))
                print(self.settings.lang_data["bot_rename_failed_continue"])
        else:
            print(self.settings.lang_data["bot_migration_failed"])
            print(self.settings.lang_data["bot_migration_failed_check"])

    async def load_cogs(self):
        """
        Load all cogs from the cogs directory.
        """
        cogs_dir = Path(__file__).parent.parent / 'cogs'
        for file in cogs_dir.glob('*.py'):
            if file.name.startswith('__'):
                continue

            # Convert file path to module path
            module_path = f"src.cogs.{file.stem}"

            try:
                # Import the module
                module = importlib.import_module(module_path)

                # Find all cog classes in the module
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, commands.Cog) and obj != commands.Cog:
                        await self.add_cog(obj(self))
                        print(self.settings.lang_data["bot_loaded_cog"].format(name))
            except Exception as e:
                print(self.settings.lang_data["bot_failed_load_cog"].format(module_path, e))

    async def on_ready(self):
        """
        Event handler for when the bot is ready.
        """
        print(self.settings.lang_data["bot_login_ok"])
        if self.application_id:
            print(self.settings.lang_data["bot_setting_url"].format(self.application_id))
            print(self.settings.lang_data["bot_invite_url"].format(self.application_id))

    @tasks.loop(seconds=10)
    async def check_twitter_updates(self):
        """
        Background task that checks for Twitter updates every 10 seconds.
        """
        # Get current time
        now_time = time.time()

        # Get all guild IDs
        guild_ids = self.db.get_all_guild_ids()
        if not guild_ids:
            # If migration is complete but no guilds in database, nothing to do
            if self.migration_done:
                return

            # If migration is not complete, try to get guild IDs from JSON
            guild_ids = self.settings.get_all_guild_ids()
            if guild_ids is None:
                return

        for guild_id in guild_ids:
            # Get guild settings from database
            guild_settings = self.db.get_guild_settings(guild_id)

            # If migration is complete but no settings for this guild, skip it
            if guild_settings is None and self.migration_done:
                continue

            # If migration is not complete and no settings in database, try JSON
            if guild_settings is None and not self.migration_done:
                # This should not happen if migration was successful, but just in case
                print(self.settings.lang_data["bot_guild_not_found"].format(guild_id))
                continue

            # Skip if Twitter updates are disabled
            if not guild_settings['twitter_updates_enabled']:
                continue

            # Get the last checked time for this guild
            last_checked_time = guild_settings['last_checked_time']

            # Check if it's time to update based on the cool down time
            if guild_settings['cool_down_minutes'] * 60 >= now_time - last_checked_time:
                # Not time yet
                continue

            # Update the last checked time for this guild
            self.db.update_guild_settings(guild_id, last_checked_time=now_time)

            # Get all Twitter feeds for this guild
            feeds = self.db.get_twitter_feeds(guild_id)

            # If no feeds, nothing to do
            if not feeds:
                continue

            # Process feeds from database
            for feed in feeds:
                await self._process_twitter_feed(guild_id, feed['channel_id'], feed['twitter_user_name'])

    async def _process_twitter_feed(self, guild_id, channel_id, twitter_user_name):
        """
        Process a single Twitter feed.

        Args:
            guild_id: The ID of the guild
            channel_id: The ID of the channel
            twitter_user_name: The Twitter username to check
        """
        # Get the channel
        channel = self.get_channel(channel_id)
        if not channel:
            return

        # Get the latest tweets
        tweet_id, next_tweet_id = await self.twitter_client.twikit_msg(twitter_user_name)
        if tweet_id is None:
            # Failed to get tweets
            print(self.settings.lang_data["bot_failed_tweets"].format(twitter_user_name))
            return

        # Get the previously seen tweet IDs from database
        old_tweet_id, old_next_tweet_id = self.db.get_tweet_history(channel_id, twitter_user_name)

        # If no history in database, initialize with zeros
        if old_tweet_id is None:
            old_tweet_id = 0
            old_next_tweet_id = 0

        # Skip if we've already seen this tweet
        if tweet_id == old_tweet_id or tweet_id == old_next_tweet_id:
            return

        # Skip if it's a retweet
        if await self.twitter_client.get_retweet(tweet_id):
            return

        # Update the stored tweet IDs in database
        self.db.update_tweet_history(channel_id, twitter_user_name, tweet_id, next_tweet_id)

        # Send the tweet to the channel
        url = f'https://fxtwitter.com/{twitter_user_name}/status/{tweet_id}'
        print(url)
        await channel.send(url, silent=True)

    @check_twitter_updates.before_loop
    async def before_check_twitter_updates(self):
        """
        Wait for the bot to be ready before starting the task.
        """
        await self.wait_until_ready()

    async def start_bot(self):
        """
        Start the bot with the token from environment variables.
        """
        if not self.token:
            raise ValueError(self.settings.lang_data["bot_no_token"])

        await self.start(self.token)

def create_bot(language='en_US'):
    """
    Create a new bot instance.

    Args:
        language (str): The language code to use (default: 'en_US')

    Returns:
        MyBot: A new bot instance
    """
    return MyBot(language)

async def run_bot(language='en_US'):
    """
    Create and run a new bot instance.

    Args:
        language (str): The language code to use (default: 'en_US')
    """
    bot = create_bot(language)
    await bot.start_bot()
