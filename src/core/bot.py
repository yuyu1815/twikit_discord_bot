import discord
import os
import time
import logging
from discord.ext import tasks, commands
from discord import app_commands
from pathlib import Path
import importlib
import inspect

from src.core.twitter_client import TwitterClient
from src.core.twitter_client_manager import TwitterClientManager
from src.config.settings import Settings
from src.core.database import Database

# Set up logging
logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(console_handler)

class MyBot(commands.Bot):
    """
    Custom Discord bot class that inherits from commands.Bot.
    This class encapsulates the core functionality of the bot, including Discord integration,
    Twitter API interaction, and database management.

    commands.Botを継承したカスタムDiscordボットクラスです。
    このクラスは、Discord連携、Twitter APIとの対話、データベース管理など、ボットのコア機能をカプセル化します。
    """

    def __init__(self, language: str = 'en_US'):
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
        # Set up Discord intents to receive only necessary events.
        # 必要なイベントのみを受信するためにDiscordのインテントを設定します。
        intents = discord.Intents.default()
        intents.guilds = True       # For server join/leave events
        intents.guild_messages = True  # For message events in servers
        intents.message_content = True  # To read message content for URL fixing

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

    async def setup_hook(self) -> None:
        """
        Set up the bot when it's starting.
        This method is called automatically by discord.py after the bot is connected.
        It loads cogs, initializes the Twitter client, performs data migration, and starts background tasks.
        
        This method ensures proper initialization sequence and error handling.

        ボットの起動時にセットアップを行います。
        このメソッドは、ボットが接続された後にdiscord.pyによって自動的に呼び出されます。
        コグのロード、Twitterクライアントの初期化、データ移行の実行、バックグラウンドタスクの開始を行います。
        
        このメソッドは、適切な初期化シーケンスとエラーハンドリングを保証します。
        """
        try:
            logger.info(self.settings.lang_data["bot_setting_up"])

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

            # Perform migration to new structure (global_twitter_users and guild_twitter_feeds)
            # 新設計（global_twitter_usersとguild_twitter_feeds）への移行を実行します。
            await self.migrate_to_new_structure_if_needed()

            # Add error handler for app commands
            self.tree.error(self.on_app_command_error)

            # Automatic tweet checking functionality is used to fetch and post tweets
            # 自動ツイートチェック機能がツイートの取得と投稿に使用されています
            
            logger.info("Bot setup completed successfully")
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}", exc_info=True)
            raise

    async def setup_for_sync(self) -> None:
        """
        Lightweight setup method for syncing slash commands only.
        This method loads cogs and sets up the command tree without initializing Twitter clients.
        
        スラッシュコマンド同期専用の軽量セットアップメソッドです。
        このメソッドはコグをロードし、Twitterクライアントの初期化なしでコマンドツリーを設定します。
        """
        try:
            logger.info("Setting up bot for command sync...")

            # Load all command extensions (cogs) from the designated directory.
            # 指定されたディレクトリからすべてのコマンド拡張機能（コグ）をロードします。
            await self.load_cogs()

            # Add error handler for app commands
            self.tree.error(self.on_app_command_error)
            
            logger.info("Bot setup for sync completed successfully")
        except Exception as e:
            logger.error(f"Error in setup_for_sync: {e}", exc_info=True)
            raise

    async def migrate_data_if_needed(self) -> None:
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
            logger.info(self.settings.lang_data.get("bot_migration_not_needed", "No JSON files to migrate, marking migration as complete"))
            return

        # Check if migration has already been completed in the database.
        # データベースで移行が既に完了しているかを確認します。
        if self.db.is_migration_completed():
            self.migration_done = True
            logger.info(self.settings.lang_data["bot_migration_completed"])
            return

        logger.info(self.settings.lang_data["bot_migration_starting"])

        # Perform the migration using the database class method.
        # データベースクラスのメソッドを使用して移行を実行します。
        success = self.db.migrate_from_json(self.settings)

        if success:
            self.migration_done = True
            logger.info(self.settings.lang_data["bot_migration_success"])

            # Rename JSON files to prevent them from being read again after successful migration.
            # 移行が成功した後、JSONファイルが再度読み込まれないように名前を変更します。
            try:
                data_dir = Path(self.settings.data_dir)
                discord_settings_file = data_dir / 'DiscordSetting.json'
                twitter_msg_file = data_dir / 'Twitter_msg.json'

                if discord_settings_file.exists():
                    discord_settings_file.rename(data_dir / 'DiscordSetting.json.migrated')
                    logger.info(self.settings.lang_data["bot_renamed_file"].format(discord_settings_file, f"{discord_settings_file}.migrated"))

                if twitter_msg_file.exists():
                    twitter_msg_file.rename(data_dir / 'Twitter_msg.json.migrated')
                    logger.info(self.settings.lang_data["bot_renamed_file"].format(twitter_msg_file, f"{twitter_msg_file}.migrated"))
            except Exception as e:
                logger.error(self.settings.lang_data["bot_rename_failed"].format(e), exc_info=e)
                logger.warning(self.settings.lang_data["bot_rename_failed_continue"])
        else:
            logger.error(self.settings.lang_data["bot_migration_failed"])
            logger.error(self.settings.lang_data["bot_migration_failed_check"])

    async def load_cogs(self) -> None:
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
                        logger.info(self.settings.lang_data["bot_loaded_cog"].format(name))
            except Exception as e:
                logger.error(self.settings.lang_data["bot_failed_load_cog"].format(module_path, e), exc_info=e)

    async def on_ready(self):
        """
        Event handler for when the bot is ready and connected to Discord.
        It prints a confirmation message and the bot's invite URL.

        ボットが準備完了し、Discordに接続されたときのイベントハンドラです。
        確認メッセージとボットの招待URLを出力します。
        """
        logger.info(self.settings.lang_data["bot_login_ok"])
        if self.application_id:
            logger.info(self.settings.lang_data["bot_setting_url"].format(self.application_id))
            logger.info(self.settings.lang_data["bot_invite_url"].format(self.application_id))
            
    async def on_command_error(self, ctx, error):
        """
        Global error handler for traditional prefix commands.
        This method is called when an error occurs during the execution of a command.
        
        従来の接頭辞コマンドのグローバルエラーハンドラー。
        このメソッドは、コマンドの実行中にエラーが発生した場合に呼び出されます。
        
        Args:
            ctx (commands.Context): The context of the command.
            error (commands.CommandError): The error that occurred.
        """
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(self.settings.lang_data.get("error_command_not_found", "Command not found."))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(self.settings.lang_data.get("error_missing_permissions", "You don't have permission to use this command."))
        else:
            logger.error(f"Command error: {error}", exc_info=error)
            await ctx.send(self.settings.lang_data.get("error_generic", "An error occurred: {0}").format(error))

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
        
        This method ensures proper startup sequence and error handling.

        環境変数から取得したトークンを使用してDiscordボットを起動します。
        トークンが見つからない場合はValueErrorを発生させます。
        
        このメソッドは、適切な起動シーケンスとエラーハンドリングを保証します。
        """
        if not self.token:
            raise ValueError(self.settings.lang_data["bot_no_token"])

        try:
            logger.info("Starting Discord bot...")
            await self.start(self.token)
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}", exc_info=True)
            raise

    async def migrate_to_new_structure_if_needed(self):
        """
        Migrate data to the new structure (global_twitter_users and guild_twitter_feeds) if needed.
        This is a one-time operation that happens at bot startup.
        """
        logger.info("Checking for new structure migration...")
        
        # Check if there's any data in the new tables
        self.db.cursor.execute("SELECT COUNT(*) FROM global_twitter_users")
        global_users_count = self.db.cursor.fetchone()[0]
        
        self.db.cursor.execute("SELECT COUNT(*) FROM guild_twitter_feeds")
        guild_feeds_count = self.db.cursor.fetchone()[0]
        
        # If both new tables are empty, perform migration
        if global_users_count == 0 and guild_feeds_count == 0:
            logger.info("Starting migration to new structure...")
            success = self.db.migrate_to_new_structure()
            if success:
                logger.info("Migration to new structure completed successfully")
            else:
                logger.error("Migration to new structure failed")
        else:
            logger.info("New structure migration not needed (data already exists)")
            
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """
        Global error handler for application commands (slash commands).
        This method is called when an error occurs during the execution of an application command.
        
        アプリケーションコマンド（スラッシュコマンド）のグローバルエラーハンドラー。
        このメソッドは、アプリケーションコマンドの実行中にエラーが発生した場合に呼び出されます。
        
        Args:
            interaction (discord.Interaction): The interaction that triggered the command.
            error (app_commands.AppCommandError): The error that occurred.
        """
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                self.settings.lang_data.get("error_command_cooldown", "This command is on cooldown. Try again in {:.2f} seconds.").format(error.retry_after),
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                self.settings.lang_data.get("error_missing_permissions", "You don't have permission to use this command."),
                ephemeral=True
            )
        else:
            logger.error(f"Application command error: {error}", exc_info=error)
            await interaction.response.send_message(
                self.settings.lang_data.get("error_generic", "An error occurred: {0}").format(error),
                ephemeral=True
            )

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
    
    This function ensures proper initialization and error handling for the bot.

    Args:
        language (str): The language code to use for the bot (default: 'en_US').

    新しいボットインスタンスを非同期で作成し、実行します。
    これはボットアプリケーションを開始するためのエントリポイントです。
    
    この関数は、ボットの適切な初期化とエラーハンドリングを保証します。

    Args:
        language (str): ボットに使用する言語コード（デフォルト: 'en_US'）。
    """
    bot = None
    try:
        # Create bot instance
        bot = create_bot(language)
        
        # Start the bot
        await bot.start_bot()
    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        if bot:
            try:
                await bot.close()
            except Exception as close_error:
                logger.error(f"Error closing bot: {close_error}")
        raise
