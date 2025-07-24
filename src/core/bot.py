import discord
import os
import time
from discord.ext import tasks, commands
from pathlib import Path
import importlib
import inspect

from src.core.twitter_client import TwitterClient
from src.core.twitter_client_manager import TwitterClientManager
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
        self.twitter_client_manager = TwitterClientManager(settings=self.settings)

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

        # Initialize the Twitter client manager, which handles both guest and authenticated clients.
        # ゲストと認証済みの両方のクライアントを処理するTwitterクライアントマネージャーを初期化します。
        await self.twitter_client_manager.initialize()

        # Perform data migration from old JSON files to the new database structure if necessary.
        # 必要に応じて、古いJSONファイルから新しいデータベース構造へのデータ移行を実行します。
        await self.migrate_data_if_needed()

        # Automatic tweet checking functionality is used to fetch and post tweets
        # 自動ツイートチェック機能がツイートの取得と投稿に使用されています

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

    # The periodic tweet checking functionality has been updated to use the TwitterClientManager.
    # 定期的なツイートチェック機能はTwitterClientManagerを使用するように更新されました。

    # The _process_twitter_feed method has been removed as it was only used by the check_twitter_updates task.
    # _process_twitter_feedメソッドはcheck_twitter_updatesタスクでのみ使用されていたため、削除されました。

    # The before_check_twitter_updates method has been removed as it was only used by the check_twitter_updates task.
    # before_check_twitter_updatesメソッドはcheck_twitter_updatesタスクでのみ使用されていたため、削除されました。

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
