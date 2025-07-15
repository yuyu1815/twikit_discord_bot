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
    This class encapsulates the core functionality of the bot, including Discord integration,
    Twitter API interaction, and database management.

    commands.Botを継承したカスタムDiscordボットクラスです。
    このクラスは、Discord連携、Twitter APIとの対話、データベース管理など、ボットのコア機能をカプセル化します。
    """

    def __init__(self, language='en_US'):
        """
        Initialize the bot with the specified language.
        It sets up Discord intents, loads environment variables, and initializes
        the settings, database, and Twitter client.

        Args:
            language (str): The language code to use (default: 'en_US').

        指定された言語でボットを初期化します。
        Discordのインテントを設定し、環境変数をロードし、設定、データベース、Twitterクライアントを初期化します。

        Args:
            language (str): 使用する言語コード（デフォルト: 'en_US'）。
        """
        # Set up Discord intents to receive necessary events.
        # 必要なイベントを受信するためにDiscordのインテントを設定します。
        intents = discord.Intents.all()

        # Load environment variables for bot token and application ID.
        # ボットのトークンとアプリケーションIDの環境変数をロードします。
        self.token = os.getenv('TOKEN')
        application_id = os.getenv('Application_ID')

        # Pass application_id to the parent class constructor.
        # 親クラスのコンストラクタにapplication_idを渡します。
        super().__init__(command_prefix='!', intents=intents, application_id=application_id)

        # Initialize settings, database, and Twitter client instances.
        # 設定、データベース、Twitterクライアントのインスタンスを初期化します。
        self.settings = Settings(language)
        self.db = Database()
        self.twitter_client = TwitterClient(settings=self.settings)

        # Flag to track if the JSON to database migration has been performed.
        # JSONからデータベースへの移行が実行されたかどうかを追跡するフラグ。
        self.migration_done = False

    async def setup_hook(self):
        """
        Set up the bot when it's starting.
        This method is called automatically by discord.py after the bot is connected.
        It loads cogs, initializes the Twitter client, performs data migration, and starts background tasks.

        ボットの起動時にセットアップを行います。
        このメソッドは、ボットが接続された後にdiscord.pyによって自動的に呼び出されます。
        コグのロード、Twitterクライアントの初期化、データ移行の実行、バックグラウンドタスクの開始を行います。
        """
        print(self.settings.lang_data["bot_setting_up"])

        # Load all command extensions (cogs) from the designated directory.
        # 指定されたディレクトリからすべてのコマンド拡張機能（コグ）をロードします。
        await self.load_cogs()

        # Initialize the Twitter client, which includes loading cookies.
        # クッキーのロードを含むTwitterクライアントを初期化します。
        await self.twitter_client.load_client()

        # Perform data migration from old JSON files to the new database structure if necessary.
        # 必要に応じて、古いJSONファイルから新しいデータベース構造へのデータ移行を実行します。
        await self.migrate_data_if_needed()

        # Start the background task for checking Twitter updates.
        # Twitterの更新をチェックするためのバックグラウンドタスクを開始します。
        self.check_twitter_updates.start()

    async def migrate_data_if_needed(self):
        """
        Migrate data from JSON files to the database if it hasn't been done yet.
        This is a one-time operation that happens at bot startup.
        After successful migration, the original JSON files are renamed to prevent them from being read again.

        JSONファイルからデータベースへのデータ移行がまだ行われていない場合に実行します。
        これはボット起動時に一度だけ行われる操作です。
        移行が成功した後、元のJSONファイルは再度読み込まれないように名前が変更されます。
        """
        data_dir = Path(self.settings.data_dir)
        discord_settings_file = data_dir / 'DiscordSetting.json'
        twitter_msg_file = data_dir / 'Twitter_msg.json'

        # If no JSON files exist, it means there's no old data to migrate, so mark migration as complete.
        # JSONファイルが存在しない場合、移行する古いデータがないため、移行を完了としてマークします。
        if not discord_settings_file.exists() and not twitter_msg_file.exists():
            self.db.set_migration_completed()
            self.migration_done = True
            # print(self.settings.lang_data["bot_migration_not_needed"])  # Optional: Add a new lang key for this
            return

        # Check if migration has already been completed in the database.
        # データベースで移行が既に完了しているかを確認します。
        if self.db.is_migration_completed():
            self.migration_done = True
            print(self.settings.lang_data["bot_migration_completed"])
            return

        print(self.settings.lang_data["bot_migration_starting"])

        # Perform the migration using the database class method.
        # データベースクラスのメソッドを使用して移行を実行します。
        success = self.db.migrate_from_json(self.settings)

        if success:
            self.migration_done = True
            print(self.settings.lang_data["bot_migration_success"])

            # Rename JSON files to prevent them from being read again after successful migration.
            # 移行が成功した後、JSONファイルが再度読み込まれないように名前を変更します。
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
        Load all cogs (extensions) from the 'cogs' directory.
        Each Python file in the 'cogs' directory is treated as a potential cog.

        'cogs'ディレクトリからすべてのコグ（拡張機能）をロードします。
        'cogs'ディレクトリ内の各Pythonファイルは、潜在的なコグとして扱われます。
        """
        cogs_dir = Path(__file__).parent.parent / 'cogs'
        for file in cogs_dir.glob('*.py'):
            # Skip __init__.py files.
            # __init__.pyファイルはスキップします。
            if file.name.startswith('__'):
                continue

            # Convert file path to a Python module path (e.g., src.cogs.my_cog).
            # ファイルパスをPythonモジュールパスに変換します（例: src.cogs.my_cog）。
            module_path = f"src.cogs.{file.stem}"

            try:
                # Import the module dynamically.
                # モジュールを動的にインポートします。
                module = importlib.import_module(module_path)

                # Iterate through members of the imported module to find and add cogs.
                # インポートされたモジュールのメンバーを反復処理し、コグを見つけて追加します。
                for name, obj in inspect.getmembers(module):
                    # Check if the object is a class, a subclass of commands.Cog, and not commands.Cog itself.
                    # オブジェクトがクラスであり、commands.Cogのサブクラスであり、かつcommands.Cog自体ではないことを確認します。
                    if inspect.isclass(obj) and issubclass(obj, commands.Cog) and obj != commands.Cog:
                        await self.add_cog(obj(self))
                        print(self.settings.lang_data["bot_loaded_cog"].format(name))
            except Exception as e:
                print(self.settings.lang_data["bot_failed_load_cog"].format(module_path, e))

    async def on_ready(self):
        """
        Event handler for when the bot is ready and connected to Discord.
        It prints a confirmation message and the bot's invite URL.

        ボットが準備完了し、Discordに接続されたときのイベントハンドラです。
        確認メッセージとボットの招待URLを出力します。
        """
        print(self.settings.lang_data["bot_login_ok"])
        if self.application_id:
            print(self.settings.lang_data["bot_setting_url"].format(self.application_id))
            print(self.settings.lang_data["bot_invite_url"].format(self.application_id))

    @tasks.loop(seconds=10)
    async def check_twitter_updates(self):
        """
        Background task that periodically checks for new Twitter updates.
        It iterates through configured guilds and their Twitter feeds,
        fetching and posting new tweets to Discord channels based on cool-down settings.

        定期的に新しいTwitterの更新をチェックするバックグラウンドタスクです。
        設定されたギルドとそのTwitterフィードを繰り返し処理し、
        クールダウン設定に基づいて新しいツイートをDiscordチャンネルに取得して投稿します。
        """
        # Get current time for cool-down calculations.
        # クールダウン計算のための現在時刻を取得します。
        now_time = time.time()

        # Get all guild IDs from the database.
        # データベースからすべてのギルドIDを取得します。
        guild_ids = self.db.get_all_guild_ids()
        if not guild_ids:
            # If migration is complete but no guilds in database, nothing to do.
            # 移行が完了しているがデータベースにギルドがない場合、何もしません。
            if self.migration_done:
                return

            # If migration is not complete, try to get guild IDs from JSON (legacy data).
            # 移行が完了していない場合、JSONからギルドIDを取得しようとします（レガシーデータ）。
            guild_ids = self.settings.get_all_guild_ids()
            if guild_ids is None:
                return

        for guild_id in guild_ids:
            # Get guild settings from the database.
            # データベースからギルド設定を取得します。
            guild_settings = self.db.get_guild_settings(guild_id)

            # If migration is complete but no settings for this guild, skip it.
            # 移行が完了しているがこのギルドの設定がない場合、スキップします。
            if guild_settings is None and self.migration_done:
                continue

            # If migration is not complete and no settings in database, this indicates an issue or a new guild.
            # 移行が完了しておらず、データベースに設定がない場合、これは問題または新しいギルドを示します。
            if guild_settings is None and not self.migration_done:
                # This should not happen if migration was successful, but just in case.
                # 移行が成功していればこれは起こらないはずですが、念のため。
                print(self.settings.lang_data["bot_guild_not_found"].format(guild_id))
                continue

            # Skip if Twitter updates are disabled for this guild.
            # このギルドのTwitter更新が無効になっている場合はスキップします。
            if not guild_settings['twitter_updates_enabled']:
                continue

            # Get the last checked time for this guild from its settings.
            # このギルドの最終チェック時刻を設定から取得します。
            last_checked_time = guild_settings['last_checked_time']

            # Check if enough time has passed since the last check based on the cool-down setting.
            # クールダウン設定に基づいて、前回のチェックから十分な時間が経過したかを確認します。
            if guild_settings['cool_down_minutes'] * 60 >= now_time - last_checked_time:
                # Not time yet, continue to the next guild.
                # まだ時間ではないため、次のギルドに進みます。
                continue

            # Update the last checked time for this guild in the database.
            # このギルドの最終チェック時刻をデータベースで更新します。
            self.db.update_guild_settings(guild_id, last_checked_time=now_time)

            # Get all Twitter feeds configured for this guild.
            # このギルドに設定されているすべてのTwitterフィードを取得します。
            feeds = self.db.get_twitter_feeds(guild_id)

            # If no feeds are configured for this guild, skip it.
            # このギルドにフィードが設定されていない場合、スキップします。
            if not feeds:
                continue

            # Process each Twitter feed for the current guild.
            # 現在のギルドの各Twitterフィードを処理します。
            for feed in feeds:
                await self._process_twitter_feed(guild_id, feed['channel_id'], feed['twitter_user_name'])

    async def _process_twitter_feed(self, guild_id, channel_id, twitter_user_name):
        """
        Process a single Twitter feed: fetch new tweets and post them to the Discord channel.

        Args:
            guild_id (int): The ID of the Discord guild.
            channel_id (int): The ID of the Discord channel where the tweet should be posted.
            twitter_user_name (str): The Twitter username to check for new tweets.

        単一のTwitterフィードを処理します：新しいツイートを取得し、Discordチャンネルに投稿します。

        Args:
            guild_id (int): DiscordギルドのID。
            channel_id (int): ツイートを投稿するDiscordチャンネルのID。
            twitter_user_name (str): 新しいツイートをチェックするTwitterユーザー名。
        """
        # Get the Discord channel object.
        # Discordチャンネルオブジェクトを取得します。
        channel = self.get_channel(channel_id)
        if not channel:
            # If the channel is not found (e.g., deleted), skip processing this feed.
            # チャンネルが見つからない場合（例: 削除された場合）、このフィードの処理をスキップします。
            return

        # Get the latest two tweet IDs from the Twitter API for the given user.
        # 指定されたユーザーのTwitter APIから最新の2つのツイートIDを取得します。
        tweet_id, next_tweet_id = await self.twitter_client.twikit_msg(twitter_user_name)
        if tweet_id is None:
            # If failed to get tweets, print an error and return.
            # ツイートの取得に失敗した場合、エラーを出力して戻ります。
            print(self.settings.lang_data["bot_failed_tweets"].format(twitter_user_name))
            return

        # Get the previously stored tweet IDs from the database for comparison.
        # 比較のために、データベースから以前に保存されたツイートIDを取得します。
        old_tweet_id, old_next_tweet_id = self.db.get_tweet_history(channel_id, twitter_user_name)

        # If no history exists in the database, initialize with zeros.
        # データベースに履歴が存在しない場合、ゼロで初期化します。
        if old_tweet_id is None:
            old_tweet_id = 0
            old_next_tweet_id = 0

        # Skip if the latest tweet has already been seen (either as the last or second last tweet).
        # 最新のツイートが既に確認済みの場合（最新または2番目に新しいツイートとして）、スキップします。
        if tweet_id == old_tweet_id or tweet_id == old_next_tweet_id:
            return

        # Skip if the latest tweet is a retweet (as per application logic).
        # 最新のツイートがリツイートの場合（アプリケーションロジックに従って）スキップします。
        if await self.twitter_client.get_retweet(tweet_id):
            return

        # Update the stored tweet IDs in the database with the new latest tweets.
        # データベースに保存されているツイートIDを新しい最新のツイートで更新します。
        self.db.update_tweet_history(channel_id, twitter_user_name, tweet_id, next_tweet_id)

        # Construct the fxtwitter.com URL for the new tweet and send it to the Discord channel.
        # 新しいツイートのfxtwitter.comのURLを構築し、Discordチャンネルに送信します。
        url = f'https://fxtwitter.com/{twitter_user_name}/status/{tweet_id}'
        print(url)
        await channel.send(url, silent=True)

    @check_twitter_updates.before_loop
    async def before_check_twitter_updates(self):
        """
        Wait for the bot to be ready before starting the `check_twitter_updates` task.
        This ensures that all necessary bot components are initialized before the loop begins.

        `check_twitter_updates`タスクを開始する前に、ボットが準備完了になるのを待ちます。
        これにより、ループが開始される前に必要なすべてのボットコンポーネントが初期化されていることが保証されます。
        """
        await self.wait_until_ready()

    async def start_bot(self):
        """
        Start the Discord bot using the token from environment variables.
        Raises a ValueError if the token is not found.

        環境変数から取得したトークンを使用してDiscordボットを起動します。
        トークンが見つからない場合はValueErrorを発生させます。
        """
        if not self.token:
            raise ValueError(self.settings.lang_data["bot_no_token"])

        await self.start(self.token)

def create_bot(language='en_US'):
    """
    Factory function to create a new instance of MyBot.

    Args:
        language (str): The language code to use for the bot (default: 'en_US').

    Returns:
        MyBot: A new bot instance.

    MyBotの新しいインスタンスを作成するためのファクトリ関数です。

    Args:
        language (str): ボットに使用する言語コード（デフォルト: 'en_US'）。

    Returns:
        MyBot: 新しいボットインスタンス。
    """
    return MyBot(language)

async def run_bot(language='en_US'):
    """
    Asynchronously creates and runs a new bot instance.
    This is the entry point for starting the bot application.

    Args:
        language (str): The language code to use for the bot (default: 'en_US').

    新しいボットインスタンスを非同期で作成し、実行します。
    これはボットアプリケーションを開始するためのエントリポイントです。

    Args:
        language (str): ボットに使用する言語コード（デフォルト: 'en_US'）。
    """
    bot = create_bot(language)
    await bot.start_bot()
