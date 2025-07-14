import sqlite3
import os
import time
from pathlib import Path

class Database:
    """
    Database class for managing all database operations.
    This class replaces the JSON-based data storage with SQLite.
    """

    def __init__(self, db_path=None):
        """
        Initialize the Database class with the specified database path.

        Args:
            db_path (str, optional): Path to the database file
        """
        self.db_path = db_path or Path(__file__).parent.parent.parent / 'data' / 'bot.db'
        self.conn = None
        self.cursor = None
        self.initialize_database()

    def initialize_database(self):
        """
        Initialize the database connection and create tables if they don't exist.
        """
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Connect to the database
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        self._create_tables()

    def _create_tables(self):
        """
        Create the necessary tables in the database.
        """
        # Create migration_info table to track migration status
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS migration_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_at INTEGER
        )
        ''')

        # Create guild_settings table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            twitter_updates_enabled BOOLEAN DEFAULT 1,
            url_preview_enabled BOOLEAN DEFAULT 1,
            cool_down_minutes INTEGER DEFAULT 1,
            last_checked_time INTEGER DEFAULT 0
        )
        ''')

        # Create twitter_feeds table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS twitter_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            twitter_user_name TEXT NOT NULL,
            UNIQUE(channel_id, twitter_user_name)
        )
        ''')

        # Create tweet_history table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweet_history (
            feed_id INTEGER PRIMARY KEY,
            last_tweet_id INTEGER DEFAULT 0,
            second_last_tweet_id INTEGER DEFAULT 0,
            FOREIGN KEY (feed_id) REFERENCES twitter_feeds(id) ON DELETE CASCADE
        )
        ''')

        # Initialize migration_info if it doesn't exist
        self.cursor.execute("SELECT 1 FROM migration_info WHERE id = 1")
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO migration_info (id, version, completed, completed_at) VALUES (1, 1, 0, NULL)"
            )

        # Commit the changes
        self.conn.commit()

    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()

    def get_guild_settings(self, guild_id):
        """
        Get the settings for a specific guild.

        Args:
            guild_id (int): The ID of the guild

        Returns:
            dict: The guild settings or None if not found
        """
        self.cursor.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        )
        row = self.cursor.fetchone()

        if row:
            return dict(row)
        else:
            return None

    def update_guild_settings(self, guild_id, twitter_updates_enabled=None, 
                             url_preview_enabled=None, cool_down_minutes=None, 
                             last_checked_time=None):
        """
        Update the settings for a specific guild.

        Args:
            guild_id (int): The ID of the guild
            twitter_updates_enabled (bool, optional): Whether Twitter updates are enabled
            url_preview_enabled (bool, optional): Whether URL previews are enabled
            cool_down_minutes (int, optional): The cool down time in minutes
            last_checked_time (int, optional): The last time tweets were checked
        """
        try:
            with self.conn:  # Use context manager for transaction
                # Get current values if they exist
                self.cursor.execute(
                    "SELECT * FROM guild_settings WHERE guild_id = ?",
                    (guild_id,)
                )
                row = self.cursor.fetchone()

                # Prepare values, using existing ones if not provided
                if row:
                    current = dict(row)
                    twitter_updates = 1 if twitter_updates_enabled else 0 if twitter_updates_enabled is not None else current['twitter_updates_enabled']
                    url_preview = 1 if url_preview_enabled else 0 if url_preview_enabled is not None else current['url_preview_enabled']
                    cool_down = cool_down_minutes if cool_down_minutes is not None else current['cool_down_minutes']
                    last_checked = last_checked_time if last_checked_time is not None else current['last_checked_time']
                else:
                    # Default values for new entry
                    twitter_updates = 1 if twitter_updates_enabled is None else (1 if twitter_updates_enabled else 0)
                    url_preview = 1 if url_preview_enabled is None else (1 if url_preview_enabled else 0)
                    cool_down = 1 if cool_down_minutes is None else cool_down_minutes
                    last_checked = 0 if last_checked_time is None else last_checked_time

                # Use INSERT OR REPLACE (UPSERT) for simpler code
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

                # No need to commit here as the context manager will do it
        except sqlite3.Error as e:
            print(f"Database error in update_guild_settings: {e}")
            # The context manager will roll back on exception

    def get_all_guild_ids(self):
        """
        Get all guild IDs from the database.

        Returns:
            list: List of guild IDs
        """
        self.cursor.execute("SELECT guild_id FROM guild_settings")
        rows = self.cursor.fetchall()
        return [row['guild_id'] for row in rows]

    def add_twitter_feed(self, guild_id, channel_id, twitter_user_name):
        """
        Add a Twitter feed for a channel.

        Args:
            guild_id (int): The ID of the guild
            channel_id (int): The ID of the channel
            twitter_user_name (str): The Twitter username to follow

        Returns:
            bool: True if successful, False if the feed already exists
        """
        try:
            with self.conn:  # Use context manager for transaction
                # Insert the feed
                self.cursor.execute(
                    """
                    INSERT INTO twitter_feeds (guild_id, channel_id, twitter_user_name)
                    VALUES (?, ?, ?)
                    """,
                    (guild_id, channel_id, twitter_user_name)
                )

                # Get the ID of the inserted feed
                feed_id = self.cursor.lastrowid

                # Initialize tweet history
                self.cursor.execute(
                    """
                    INSERT INTO tweet_history (feed_id, last_tweet_id, second_last_tweet_id)
                    VALUES (?, 0, 0)
                    """,
                    (feed_id,)
                )

                # No need to commit here as the context manager will do it
                return True
        except sqlite3.IntegrityError:
            # Feed already exists
            return False
        except sqlite3.Error as e:
            print(f"Database error in add_twitter_feed: {e}")
            # The context manager will roll back on exception
            return False

    def remove_twitter_feed(self, channel_id, twitter_user_name):
        """
        Remove a Twitter feed from a channel.

        Args:
            channel_id (int): The ID of the channel
            twitter_user_name (str): The Twitter username to unfollow

        Returns:
            bool: True if successful, False if the feed doesn't exist
        """
        try:
            with self.conn:  # Use context manager for transaction
                # Get the feed ID
                self.cursor.execute(
                    """
                    SELECT id FROM twitter_feeds
                    WHERE channel_id = ? AND twitter_user_name = ?
                    """,
                    (channel_id, twitter_user_name)
                )
                row = self.cursor.fetchone()

                if not row:
                    return False

                feed_id = row['id']

                # Delete the tweet history
                self.cursor.execute(
                    "DELETE FROM tweet_history WHERE feed_id = ?",
                    (feed_id,)
                )

                # Delete the feed
                self.cursor.execute(
                    """
                    DELETE FROM twitter_feeds
                    WHERE id = ?
                    """,
                    (feed_id,)
                )

                # No need to commit here as the context manager will do it
                return True
        except sqlite3.Error as e:
            print(f"Database error in remove_twitter_feed: {e}")
            # The context manager will roll back on exception
            return False

    def get_twitter_feeds(self, guild_id):
        """
        Get all Twitter feeds for a guild.

        Args:
            guild_id (int): The ID of the guild

        Returns:
            list: List of dictionaries containing channel_id and twitter_user_name
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
        Get the tweet history for a specific channel and Twitter username.

        Args:
            channel_id (int): The ID of the channel
            twitter_user_name (str): The Twitter username

        Returns:
            tuple: (last_tweet_id, second_last_tweet_id) or (None, None) if not found
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
        Update the tweet history for a specific channel and Twitter username.

        Args:
            channel_id (int): The ID of the channel
            twitter_user_name (str): The Twitter username
            last_tweet_id (int): The ID of the last tweet
            second_last_tweet_id (int): The ID of the second last tweet

        Returns:
            bool: True if successful, False if the feed doesn't exist
        """
        try:
            with self.conn:  # Use context manager for transaction
                # Get the feed ID
                self.cursor.execute(
                    """
                    SELECT id FROM twitter_feeds
                    WHERE channel_id = ? AND twitter_user_name = ?
                    """,
                    (channel_id, twitter_user_name)
                )
                row = self.cursor.fetchone()

                if not row:
                    return False

                feed_id = row['id']

                # Update the tweet history
                self.cursor.execute(
                    """
                    UPDATE tweet_history
                    SET last_tweet_id = ?, second_last_tweet_id = ?
                    WHERE feed_id = ?
                    """,
                    (last_tweet_id, second_last_tweet_id, feed_id)
                )

                # No need to commit here as the context manager will do it
                return True
        except sqlite3.Error as e:
            print(f"Database error in update_tweet_history: {e}")
            # The context manager will roll back on exception
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
                    return False

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
