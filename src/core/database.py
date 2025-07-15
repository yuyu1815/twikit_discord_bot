import sqlite3
import os
import time
from pathlib import Path

class Database:
    """
    Database class for managing all database operations.
    This class replaces the JSON-based data storage with SQLite, providing a more robust and scalable solution.

    データベース操作を管理するためのデータベースクラスです。
    このクラスは、JSONベースのデータストレージをSQLiteに置き換え、より堅牢でスケーラブルなソリューションを提供します。
    """

    def __init__(self, db_path=None):
        """
        Initialize the Database class with the specified database path.
        If no path is provided, it defaults to 'data/bot.db'.

        Args:
            db_path (str, optional): Path to the database file. Defaults to None.

        指定されたデータベースパスでデータベースクラスを初期化します。
        パスが指定されない場合、デフォルトで 'data/bot.db' を使用します。

        Args:
            db_path (str, optional): データベースファイルのパス。デフォルトはNone。
        """
        # Determine the database file path. Defaults to 'data/bot.db'.
        # データベースファイルのパスを決定します。デフォルトは 'data/bot.db' です。
        self.db_path = db_path or Path(__file__).parent.parent.parent / 'data' / 'bot.db'
        self.conn = None
        self.cursor = None
        self.initialize_database()

    def initialize_database(self):
        """
        Initialize the database connection and create tables if they don't exist.
        This method ensures that the database file and necessary tables are set up correctly.

        データベース接続を初期化し、テーブルが存在しない場合は作成します。
        このメソッドは、データベースファイルと必要なテーブルが正しく設定されていることを保証します。
        """
        # Create the directory for the database file if it doesn't exist.
        # データベースファイルのディレクトリが存在しない場合は作成します。
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Connect to the SQLite database.
        # SQLiteデータベースに接続します。
        self.conn = sqlite3.connect(str(self.db_path))
        # Set row_factory to sqlite3.Row to access columns by name.
        # カラム名を指定してアクセスできるように、row_factoryをsqlite3.Rowに設定します。
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Create tables if they do not already exist.
        # テーブルがまだ存在しない場合は作成します。
        self._create_tables()

    def _create_tables(self):
        """
        Create the necessary tables in the database.
        This is an internal helper method called during database initialization.

        データベースに必要なテーブルを作成します。
        これはデータベース初期化中に呼び出される内部ヘルパーメソッドです。
        """
        # Create migration_info table to track migration status from JSON to DB.
        # JSONからDBへの移行状況を追跡するためのmigration_infoテーブルを作成します。
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_at INTEGER
        )
        ''')

        # Create guild_settings table to store configuration for each Discord guild.
        # 各Discordギルドの設定を保存するためのguild_settingsテーブルを作成します。
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            twitter_updates_enabled BOOLEAN DEFAULT 1,
            url_preview_enabled BOOLEAN DEFAULT 1,
            cool_down_minutes INTEGER DEFAULT 1,
            last_checked_time INTEGER DEFAULT 0
        )
        ''')

        # Create twitter_feeds table to store Twitter feeds configured for channels.
        # チャンネルに設定されたTwitterフィードを保存するためのtwitter_feedsテーブルを作成します。
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS twitter_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            twitter_user_name TEXT NOT NULL,
            UNIQUE(channel_id, twitter_user_name)
        )
        ''')

        # Create tweet_history table to store the last two tweet IDs for each feed.
        # 各フィードの最新2つのツイートIDを保存するためのtweet_historyテーブルを作成します。
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweet_history (
            feed_id INTEGER PRIMARY KEY,
            last_tweet_id INTEGER DEFAULT 0,
            second_last_tweet_id INTEGER DEFAULT 0,
            FOREIGN KEY (feed_id) REFERENCES twitter_feeds(id) ON DELETE CASCADE
        )
        '''
        # Initialize migration_info if it doesn't exist. This ensures the migration status is tracked.
        # migration_infoが存在しない場合は初期化します。これにより、移行ステータスが追跡されます。
        self.cursor.execute("SELECT 1 FROM migration_info WHERE id = 1")
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO migration_info (id, version, completed, completed_at) VALUES (1, 1, 0, NULL)"
            )

        # Commit the changes to the database.
        # データベースへの変更をコミットします。
        self.conn.commit()

    def close(self):
        """
        Close the database connection.
        It's important to close the connection when the application shuts down to release resources.

        データベース接続を閉じます。
        リソースを解放するために、アプリケーションがシャットダウンするときに接続を閉じることが重要です。
        """
        if self.conn:
            self.conn.close()

    def get_guild_settings(self, guild_id):
        """
        Retrieve the settings for a specific Discord guild.

        Args:
            guild_id (int): The ID of the Discord guild.

        Returns:
            dict: A dictionary containing the guild settings if found, otherwise None.

        特定のDiscordギルドの設定を取得します。

        Args:
            guild_id (int): DiscordギルドのID。

        Returns:
            dict: 見つかった場合はギルド設定を含む辞書、それ以外の場合はNone。
        """
        self.cursor.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        )
        row = self.cursor.fetchone()

        if row:
            # Convert sqlite3.Row object to a dictionary.
            # sqlite3.Rowオブジェクトを辞書に変換します。
            return dict(row)
        else:
            return None

    def update_guild_settings(self, guild_id, twitter_updates_enabled=None, 
                             url_preview_enabled=None, cool_down_minutes=None, 
                             last_checked_time=None):
        """
        Update the settings for a specific Discord guild.
        If a setting is not provided, its current value will be retained.
        If the guild does not exist, a new entry will be created with default values for unspecified settings.

        Args:
            guild_id (int): The ID of the Discord guild.
            twitter_updates_enabled (bool, optional): Whether Twitter updates are enabled for the guild. Defaults to None.
            url_preview_enabled (bool, optional): Whether URL previews are enabled for the guild. Defaults to None.
            cool_down_minutes (int, optional): The cool down time in minutes for tweet checks. Defaults to None.
            last_checked_time (int, optional): The Unix timestamp of the last tweet check. Defaults to None.

        特定のDiscordギルドの設定を更新します。
        設定が提供されない場合、現在の値が保持されます。
        ギルドが存在しない場合、指定されていない設定にはデフォルト値が設定された新しいエントリが作成されます。

        Args:
            guild_id (int): DiscordギルドのID。
            twitter_updates_enabled (bool, optional): ギルドのTwitter更新が有効かどうか。デフォルトはNone。
            url_preview_enabled (bool, optional): ギルドのURLプレビューが有効かどうか。デフォルトはNone。
            cool_down_minutes (int, optional): ツイートチェックのクールダウン時間（分）。デフォルトはNone。
            last_checked_time (int, optional): 最後にツイートがチェックされたUnixタイムスタンプ。デフォルトはNone。
        """
        try:
            # Use a context manager for transaction management (commit on success, rollback on error).
            # トランザクション管理のためにコンテキストマネージャーを使用します（成功時にコミット、エラー時にロールバック）。
            with self.conn:
                # Get current values if the guild settings already exist.
                # ギルド設定が既に存在する場合、現在の値を取得します。
                self.cursor.execute(
                    "SELECT * FROM guild_settings WHERE guild_id = ?",
                    (guild_id,)
                )
                row = self.cursor.fetchone()

                # Prepare values for update/insert, using existing ones if not provided.
                # 更新/挿入のための値を準備します。提供されない場合は既存の値を使用します。
                if row:
                    current = dict(row)
                    twitter_updates = 1 if twitter_updates_enabled else 0 if twitter_updates_enabled is not None else current['twitter_updates_enabled']
                    url_preview = 1 if url_preview_enabled else 0 if url_preview_enabled is not None else current['url_preview_enabled']
                    cool_down = cool_down_minutes if cool_down_minutes is not None else current['cool_down_minutes']
                    last_checked = last_checked_time if last_checked_time is not None else current['last_checked_time']
                else:
                    # Default values for a new entry if the guild settings do not exist.
                    # ギルド設定が存在しない場合の新しいエントリのデフォルト値。
                    twitter_updates = 1 if twitter_updates_enabled is None else (1 if twitter_updates_enabled else 0)
                    url_preview = 1 if url_preview_enabled is None else (1 if url_preview_enabled else 0)
                    cool_down = 1 if cool_down_minutes is None else cool_down_minutes
                    last_checked = 0 if last_checked_time is None else last_checked_time

                # Use INSERT OR REPLACE (UPSERT) for simpler code to either insert a new row or update an existing one.
                # 新しい行を挿入するか、既存の行を更新するために、INSERT OR REPLACE (UPSERT) を使用します。
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO guild_settings 
                    (guild_id, twitter_updates_enabled, url_preview_enabled, cool_down_minutes, last_checked_time)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        guild_id,
                        twitter_updates,
                        url_preview,
                        cool_down,
                        last_checked
                    )
                )

                # The context manager automatically commits the transaction on successful exit.
                # コンテキストマネージャーは、正常終了時にトランザクションを自動的にコミットします。
        except sqlite3.Error as e:
            print(f"Database error in update_guild_settings: {e}")
            # The context manager will automatically roll back the transaction on exception.
            # コンテキストマネージャーは、例外発生時にトランザクションを自動的にロールバックします。

    def get_all_guild_ids(self):
        """
        Retrieve all unique guild IDs from the database that have settings or feeds configured.

        Returns:
            list: A list of integer guild IDs.

        設定またはフィードが設定されているデータベースから、すべての一意のギルドIDを取得します。

        Returns:
            list: 整数型のギルドIDのリスト。
        """
        self.cursor.execute("SELECT guild_id FROM guild_settings")
        rows = self.cursor.fetchall()
        return [row['guild_id'] for row in rows]

    def add_twitter_feed(self, guild_id, channel_id, twitter_user_name):
        """
        Add a new Twitter feed entry for a specific channel within a guild.
        This also initializes the tweet history for the new feed.

        Args:
            guild_id (int): The ID of the Discord guild.
            channel_id (int): The ID of the Discord channel where the feed will be active.
            twitter_user_name (str): The Twitter username to follow for this feed.

        Returns:
            bool: True if the feed was successfully added, False if a feed with the same channel and username already exists.

        ギルド内の特定のチャンネルに新しいTwitterフィードエントリを追加します。
        これにより、新しいフィードのツイート履歴も初期化されます。

        Args:
            guild_id (int): DiscordギルドのID。
            channel_id (int): フィードがアクティブになるDiscordチャンネルのID。
            twitter_user_name (str): このフィードでフォローするTwitterユーザー名。

        Returns:
            bool: フィードが正常に追加された場合はTrue、同じチャンネルとユーザー名を持つフィードが既に存在する場合はFalse。
        """
        try:
            with self.conn:  # Use context manager for transaction.
                # Insert the new Twitter feed into the twitter_feeds table.
                # 新しいTwitterフィードをtwitter_feedsテーブルに挿入します。
                self.cursor.execute(
                    """
                    INSERT INTO twitter_feeds (guild_id, channel_id, twitter_user_name)
                    VALUES (?, ?, ?)
                    """,
                    (guild_id, channel_id, twitter_user_name)
                )

                # Get the ID of the newly inserted feed to link it to tweet history.
                # 新しく挿入されたフィードのIDを取得し、ツイート履歴にリンクします。
                feed_id = self.cursor.lastrowid

                # Initialize tweet history for the new feed with default values.
                # 新しいフィードのツイート履歴をデフォルト値で初期化します。
                self.cursor.execute(
                    """
                    INSERT INTO tweet_history (feed_id, last_tweet_id, second_last_tweet_id)
                    VALUES (?, 0, 0)
                    """,
                    (feed_id,)
                )

                return True
        except sqlite3.IntegrityError:
            # This exception is caught if a feed with the same channel_id and twitter_user_name already exists (UNIQUE constraint).
            # 同じchannel_idとtwitter_user_nameを持つフィードが既に存在する場合（UNIQUE制約）、この例外が捕捉されます。
            return False
        except sqlite3.Error as e:
            print(f"Database error in add_twitter_feed: {e}")
            return False

    def remove_twitter_feed(self, channel_id, twitter_user_name):
        """
        Remove an existing Twitter feed from a channel.
        This also deletes the associated tweet history.

        Args:
            channel_id (int): The ID of the Discord channel from which to remove the feed.
            twitter_user_name (str): The Twitter username of the feed to remove.

        Returns:
            bool: True if the feed was successfully removed, False if the feed did not exist.

        既存のTwitterフィードをチャンネルから削除します。
        これにより、関連するツイート履歴も削除されます。

        Args:
            channel_id (int): フィードを削除するDiscordチャンネルのID。
            twitter_user_name (str): 削除するフィードのTwitterユーザー名。

        Returns:
            bool: フィードが正常に削除された場合はTrue、フィードが存在しなかった場合はFalse。
        """
        try:
            with self.conn:  # Use context manager for transaction.
                # First, retrieve the feed_id based on channel_id and twitter_user_name.
                # まず、channel_idとtwitter_user_nameに基づいてfeed_idを取得します。
                self.cursor.execute(
                    """
                    SELECT id FROM twitter_feeds
                    WHERE channel_id = ? AND twitter_user_name = ?
                    """,
                    (channel_id, twitter_user_name)
                )
                row = self.cursor.fetchone()

                if not row:
                    # If no matching feed is found, return False.
                    # 一致するフィードが見つからない場合、Falseを返します。
                    return False

                feed_id = row['id']

                # Delete the associated tweet history entry.
                # 関連するツイート履歴エントリを削除します。
                self.cursor.execute(
                    "DELETE FROM tweet_history WHERE feed_id = ?",
                    (feed_id,)
                )

                # Delete the Twitter feed entry itself.
                # Twitterフィードエントリ自体を削除します。
                self.cursor.execute(
                    """
                    DELETE FROM twitter_feeds
                    WHERE id = ?
                    """,
                    (feed_id,)
                )

                return True
        except sqlite3.Error as e:
            print(f"Database error in remove_twitter_feed: {e}")
            return False

    def get_twitter_feeds(self, guild_id):
        """
        Retrieve all Twitter feeds configured for a specific Discord guild.

        Args:
            guild_id (int): The ID of the Discord guild.

        Returns:
            list: A list of dictionaries, each containing 'channel_id' and 'twitter_user_name' for the feeds.

        特定のDiscordギルドに設定されているすべてのTwitterフィードを取得します。

        Returns:
            list: 各フィードの 'channel_id' と 'twitter_user_name' を含む辞書のリスト。
        """
        self.cursor.execute(
            """
            SELECT channel_id, twitter_user_name FROM twitter_feeds
            WHERE guild_id = ?
            """,
            (guild_id,)
        )
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_tweet_history(self, channel_id, twitter_user_name):
        """
        Retrieve the last two tweet IDs for a specific Twitter feed.

        Args:
            channel_id (int): The ID of the Discord channel associated with the feed.
            twitter_user_name (str): The Twitter username associated with the feed.

        Returns:
            tuple: A tuple containing (last_tweet_id, second_last_tweet_id) if found, otherwise (None, None).

        特定のTwitterフィードの最新2つのツイートIDを取得します。

        Args:
            channel_id (int): フィードに関連付けられたDiscordチャンネルのID。
            twitter_user_name (str): フィードに関連付けられたTwitterユーザー名。

        Returns:
            tuple: 見つかった場合は (last_tweet_id, second_last_tweet_id) のタプル、それ以外の場合は (None, None)。
        """
        self.cursor.execute(
            """
            SELECT th.last_tweet_id, th.second_last_tweet_id
            FROM tweet_history th
            JOIN twitter_feeds tf ON th.feed_id = tf.id
            WHERE tf.channel_id = ? AND tf.twitter_user_name = ?
            """,
            (channel_id, twitter_user_name)
        )
        row = self.cursor.fetchone()

        if row:
            return row['last_tweet_id'], row['second_last_tweet_id']
        else:
            return None, None

    def update_tweet_history(self, channel_id, twitter_user_name, last_tweet_id, second_last_tweet_id):
        """
        Update the tweet history (last two tweet IDs) for a specific Twitter feed.

        Args:
            channel_id (int): The ID of the Discord channel associated with the feed.
            twitter_user_name (str): The Twitter username associated with the feed.
            last_tweet_id (int): The ID of the most recent tweet.
            second_last_tweet_id (int): The ID of the second most recent tweet.

        Returns:
            bool: True if the history was successfully updated, False if the feed did not exist.

        特定のTwitterフィードのツイート履歴（最新2つのツイートID）を更新します。

        Args:
            channel_id (int): フィードに関連付けられたDiscordチャンネルのID。
            twitter_user_name (str): フィードに関連付けられたTwitterユーザー名。
            last_tweet_id (int): 最新のツイートID。
            second_last_tweet_id (int): 2番目に新しいツイートID。

        Returns:
            bool: 履歴が正常に更新された場合はTrue、フィードが存在しなかった場合はFalse。
        """
        try:
            with self.conn:  # Use context manager for transaction.
                # Get the feed_id based on channel_id and twitter_user_name.
                # channel_idとtwitter_user_nameに基づいてfeed_idを取得します。
                self.cursor.execute(
                    """
                    SELECT id FROM twitter_feeds
                    WHERE channel_id = ? AND twitter_user_name = ?
                    """,
                    (channel_id, twitter_user_name)
                )
                row = self.cursor.fetchone()

                if not row:
                    # If no matching feed is found, return False.
                    # 一致するフィードが見つからない場合、Falseを返します。
                    return False

                feed_id = row['id']

                # Update the last_tweet_id and second_last_tweet_id for the found feed.
                # 見つかったフィードのlast_tweet_idとsecond_last_tweet_idを更新します。
                self.cursor.execute(
                    """
                    UPDATE tweet_history
                    SET last_tweet_id = ?, second_last_tweet_id = ?
                    WHERE feed_id = ?
                    """,
                    (last_tweet_id, second_last_tweet_id, feed_id)
                )

                return True
        except sqlite3.Error as e:
            print(f"Database error in update_tweet_history: {e}")
            return False

    def is_migration_completed(self):
        """
        Check if the migration from JSON to database has been completed.

        Returns:
            bool: True if migration has been completed, False otherwise
        """
        self.cursor.execute("SELECT completed FROM migration_info WHERE id = 1")
        row = self.cursor.fetchone()
        return bool(row and row['completed'])

    def set_migration_completed(self):
        """
        Mark the migration as completed.
        """
        try:
            with self.conn:
                self.cursor.execute(
                    "UPDATE migration_info SET completed = 1, completed_at = ? WHERE id = 1",
                    (int(time.time()),)
                )
        except sqlite3.Error as e:
            print(f"Database error in set_migration_completed: {e}")

    def migrate_from_json(self, settings):
        """
        Migrate data from JSON files to the database.

        Args:
            settings: The Settings instance containing JSON data

        Returns:
            bool: True if migration was successful, False otherwise
        """
        # Check if migration has already been completed
        if self.is_migration_completed():
            print("Migration has already been completed.")
            return True

        try:
            with self.conn:  # Use context manager for transaction
                # Get all guild IDs
                guild_ids = settings.get_all_guild_ids()
                if not guild_ids:
                    print("No guild IDs found in JSON files.")
                    # If no guild IDs found, consider migration successful (nothing to migrate)
                    self.set_migration_completed()
                    return True

                # Migrate each guild's settings
                for guild_id in guild_ids:
                    # Get guild config
                    json_data = settings.get_guild_config(guild_id)
                    if not json_data:
                        continue

                    print(f"Migrating guild {guild_id}...")

                    # Update guild settings
                    self.cursor.execute(
                        """
                        INSERT OR REPLACE INTO guild_settings 
                        (guild_id, twitter_updates_enabled, url_preview_enabled, cool_down_minutes, last_checked_time)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            int(guild_id),
                            1 if json_data["setting_bool"][0] else 0,
                            1 if json_data["setting_bool"][1] else 0,
                            json_data["cool_down_time"],
                            json_data.get("last_checked_time", 0)
                        )
                    )

                    # Add Twitter feeds
                    for channel_id, twitter_user_name in zip(json_data["setting_channels"], json_data["twitter_user_names"]):
                        try:
                            # Insert the feed
                            self.cursor.execute(
                                """
                                INSERT INTO twitter_feeds (guild_id, channel_id, twitter_user_name)
                                VALUES (?, ?, ?)
                                """,
                                (int(guild_id), channel_id, twitter_user_name)
                            )

                            # Get the ID of the inserted feed
                            feed_id = self.cursor.lastrowid

                            # Get tweet history
                            tweet_ids = settings.get_twitter_msg(channel_id, twitter_user_name)

                            # Initialize tweet history
                            self.cursor.execute(
                                """
                                INSERT INTO tweet_history (feed_id, last_tweet_id, second_last_tweet_id)
                                VALUES (?, ?, ?)
                                """,
                                (
                                    feed_id,
                                    tweet_ids[0] if tweet_ids and tweet_ids[0] is not None else 0,
                                    tweet_ids[1] if tweet_ids and tweet_ids[1] is not None else 0
                                )
                            )
                        except sqlite3.IntegrityError:
                            # Feed already exists, update tweet history if needed
                            print(f"Feed already exists for channel {channel_id} and user {twitter_user_name}")

                            # Get the feed ID
                            self.cursor.execute(
                                """
                                SELECT id FROM twitter_feeds
                                WHERE channel_id = ? AND twitter_user_name = ?
                                """,
                                (channel_id, twitter_user_name)
                            )
                            row = self.cursor.fetchone()

                            if row:
                                feed_id = row['id']

                                # Get tweet history
                                tweet_ids = settings.get_twitter_msg(channel_id, twitter_user_name)
                                if tweet_ids and tweet_ids[0] is not None:
                                    # Update tweet history
                                    self.cursor.execute(
                                        """
                                        UPDATE tweet_history
                                        SET last_tweet_id = ?, second_last_tweet_id = ?
                                        WHERE feed_id = ?
                                        """,
                                        (tweet_ids[0], tweet_ids[1] or 0, feed_id)
                                    )

                # Mark migration as completed
                self.set_migration_completed()
                print("Migration completed successfully.")
                return True
        except Exception as e:
            print(f"Error during migration: {e}")
            # The context manager will roll back on exception
            return False
