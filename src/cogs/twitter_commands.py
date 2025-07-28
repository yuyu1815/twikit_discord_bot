import discord
import time
import os
import logging
import asyncio
from discord import app_commands
from discord.ext import commands, tasks
from pathlib import Path

from src.core.twitter_analyzer import get_latest_tweets_with_manager, analyze_tweet_with_manager

# Set up logging
logger = logging.getLogger('twitter_commands')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='twitter_commands.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(console_handler)

class TwitterCommandsCog(commands.Cog):
    """
    Cog for Twitter-related commands.
    This includes commands for setting up Twitter feeds, checking settings, etc.

    Twitter関連コマンドのコグです。
    Twitterフィードの設定、設定の確認などのコマンドが含まれます。
    """

    def __init__(self, bot):
        """
        Initialize the cog with a reference to the bot.
        The bot instance provides access to settings, database, and Twitter client.

        Args:
            bot: The bot instance (MyBot).

        ボットへの参照でコグを初期化します。
        ボットインスタンスは、設定、データベース、Twitterクライアントへのアクセスを提供します。

        Args:
            bot: ボットインスタンス (MyBot)。
        """
        self.bot = bot
        self.lang = bot.settings.lang_data

        # Start the automatic tweet checking task with the minimum cooldown time
        # 最小クールダウン時間で自動ツイートチェックタスクを開始
        self.update_check_interval()

    async def message_send(self, interaction, msg, ephemeral=False):
        """
        Send a message to both Discord (via interaction response) and the console.

        Args:
            interaction: The interaction object from Discord.
            msg: The message string to send.
            ephemeral (bool, optional): Whether the message should be ephemeral (only visible to the user who invoked the command). Defaults to False.

        Discord（インタラクション応答経由）とコンソールの両方にメッセージを送信します。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            msg: 送信するメッセージ文字列。
            ephemeral (bool, optional): メッセージが一時的（コマンドを呼び出したユーザーのみに表示）であるかどうか。デフォルトはFalse。
        """
        logger.info(self.lang.get("twitter_commands_message_log", "{0}").format(msg))
        await interaction.response.send_message(msg, ephemeral=ephemeral)

    @tasks.loop(seconds=60)
    async def loop(self):
        """
        すべてのTwitterユーザーを一度だけAPI取得し、
        新ツイートがあれば紐付く全ギルド・チャンネルへ送信する新設計ループ。
        """
        now_time = time.time()
        twitter_users = self.bot.db.get_all_twitter_users()
        if not twitter_users:
            return
        for twitter_user_name in twitter_users:
            user_data = self.bot.db.get_global_twitter_user(twitter_user_name)
            if not user_data:
                continue
            last_updated = user_data['last_updated']
            # グローバルクールダウン（例: 1分）
            if (now_time - last_updated) < 60:
                continue
            # 最新ツイート取得
            tweets = await get_latest_tweets_with_manager(
                self.bot.twitter_client_manager,
                screen_name=twitter_user_name,
                count=10
            )
            if not tweets:
                continue
            last_tweet_id = user_data['last_tweet_id']
            new_tweets = []
            for tweet in tweets:
                tweet_id = int(tweet.id)
                if last_tweet_id and tweet_id == int(last_tweet_id):
                    continue
                if not last_tweet_id or tweet_id > int(last_tweet_id):
                    new_tweets.append(tweet)
            if not new_tweets:
                continue
            # 最新ツイート情報をグローバルに更新
            most_recent_tweet = new_tweets[-1]
            most_recent_tweet_url = f"https://fxtwitter.com/{twitter_user_name}/status/{most_recent_tweet.id}"
            self.bot.db.update_global_twitter_user(
                twitter_user_name,
                most_recent_tweet.id,
                most_recent_tweet_url,
                last_tweet_id,
                user_data['last_tweet_url']
            )
            # このユーザーをフォローしているギルド・チャンネルへ送信
            guilds = self.bot.db.get_guilds_for_twitter_user(twitter_user_name)
            for guild_data in guilds:
                guild_id = guild_data['guild_id']
                channel_id = guild_data['channel_id']
                guild_settings = self.bot.db.get_guild_settings(guild_id)
                if not guild_settings or not guild_settings.get('twitter_updates_enabled', False):
                    continue
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue
                tweet_type_filter = guild_settings.get('tweet_type_filter', 'original')
                tweet_types = tweet_type_filter.split(',')
                for tweet in new_tweets:
                    analysis = await analyze_tweet_with_manager(self.bot.twitter_client_manager, tweet.id)
                    tweet_type = analysis.get('type', 'unknown')
                    if tweet_type not in tweet_types and 'all' not in tweet_types:
                        continue
                    await self._send_tweet_embed(channel, tweet, analysis)
                    url = f'https://fxtwitter.com/{twitter_user_name}/status/{tweet.id}'
                    await channel.send(url, silent=True)

    @loop.before_loop
    async def before_loop(self):
        """
        Wait until the bot is ready before starting the loop task.

        loopタスクを開始する前に、ボットの準備が整うまで待ちます。
        """
        await self.bot.wait_until_ready()
        
    @loop.error
    async def loop_error(self, error):
        """
        Error handler for the loop task.
        This method is called when an error occurs during the execution of the loop task.
        
        loopタスクのエラーハンドラー。
        このメソッドは、loopタスクの実行中にエラーが発生した場合に呼び出されます。
        
        Args:
            error (Exception): The error that occurred.
        """
        logger.error(f"Error in loop task: {error}", exc_info=error)
        # Restart the task after a short delay
        self.loop.cancel()
        await asyncio.sleep(5)
        self.loop.start()

    async def _send_tweet_embed(self, channel, tweet, analysis):
        """
        Create and send an embed for a tweet to a Discord channel.

        Args:
            channel: The Discord channel to send the embed to.
            tweet: The tweet object.
            analysis: The analysis of the tweet from analyze_tweet_with_manager.

        ツイートのembedを作成し、Discordチャンネルに送信します。

        Args:
            channel: embedを送信するDiscordチャンネル。
            tweet: ツイートオブジェクト。
            analysis: analyze_tweet_with_managerからのツイートの分析。
        """
        try:
            # Create the embed
            embed = discord.Embed(
                title=f"@{tweet.user.screen_name}",
                description=tweet.text,
                url=f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                color=0x1DA1F2  # Twitter blue
            )

            # Add author info
            embed.set_author(
                name=f"{tweet.user.name} (@{tweet.user.screen_name})",
                url=f"https://twitter.com/{tweet.user.screen_name}",
                icon_url=tweet.user.profile_image_url
            )

            # Add timestamp
            if hasattr(tweet, 'created_at'):
                embed.timestamp = tweet.created_at

            # Add footer based on tweet type
            tweet_type = analysis.get('type', 'unknown')
            if tweet_type == 'retweet' and 'original_tweet' in analysis:
                original_user = analysis['original_tweet']['user_screen_name']
                embed.set_footer(text=f"Retweet of @{original_user}")
            elif tweet_type == 'reply' and 'reply_thread' in analysis:
                reply_to = analysis['reply_thread'][0]['user_screen_name'] if analysis['reply_thread'] else "someone"
                embed.set_footer(text=f"Reply to @{reply_to}")
            else:
                embed.set_footer(text="Tweet")

            # Add fxtwitter.com URL for better embedding
            fx_url = f"https://fxtwitter.com/{tweet.user.screen_name}/status/{tweet.id}"
            embed.add_field(name="Link", value=fx_url, inline=False)

            # Send the embed
            await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending tweet embed: {e}", exc_info=e)

    @app_commands.command(
        name='set_twitter',
        description="Set up automatic Twitter feed tracking for a specific Twitter user in this channel"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_command(self, interaction: discord.Interaction, twitter_user_name: str):
        """
        Set up a Twitter feed for the current channel.
        This command allows administrators to specify a Twitter username to track.
        The bot will automatically fetch and post new tweets from this user to the channel.
        
        If the Twitter user doesn't exist, the command will fail with an error message.
        If the Twitter user is already being tracked in this channel, the command will fail with an error message.
        
        Example usage:
        /set_twitter twitter_user_name:elonmusk - Tracks tweets from @elonmusk
        
        Note: You must have the "Manage Channels" permission to use this command.

        Args:
            interaction: The interaction object from Discord.
            twitter_user_name (str): The Twitter username to follow for updates (without the @ symbol).

        現在のチャンネルにTwitterフィードを設定します。
        このコマンドは、管理者が追跡するTwitterユーザー名を指定することを可能にします。
        ボットは自動的にこのユーザーからの新しいツイートを取得し、チャンネルに投稿します。
        
        Twitterユーザーが存在しない場合、コマンドはエラーメッセージで失敗します。
        Twitterユーザーがすでにこのチャンネルで追跡されている場合、コマンドはエラーメッセージで失敗します。
        
        使用例：
        /set_twitter twitter_user_name:elonmusk - @elonmuskからのツイートを追跡します
        
        注意：このコマンドを使用するには「チャンネルの管理」権限が必要です。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            twitter_user_name (str): 更新をフォローするTwitterユーザー名（@記号なし）。
        """
        # Get channel and guild IDs from the interaction.
        # インタラクションからチャンネルIDとギルドIDを取得します。
        channel_id = interaction.channel_id
        guild_id = interaction.guild_id

        # Retrieve guild settings from the database.
        # データベースからギルド設定を取得します。
        guild_settings = self.bot.db.get_guild_settings(guild_id)

        # If no settings exist for the guild, create default settings.
        # ギルドの設定が存在しない場合、デフォルト設定を作成します。
        if guild_settings is None:
            self.bot.db.update_guild_settings(
                guild_id,
                twitter_updates_enabled=True,
                url_preview_enabled=True,
                cool_down_minutes=1
            )
            guild_settings = self.bot.db.get_guild_settings(guild_id)

            # Update the check interval as new guild settings might affect the minimum cooldown
            # 新しいギルド設定が最小クールダウンに影響する可能性があるため、チェック間隔を更新します
            self.update_check_interval()

        # Check if Twitter updates are enabled for this guild.
        # このギルドでTwitterの更新が有効になっているかを確認します。
        if not guild_settings['twitter_updates_enabled']:
            await self.message_send(interaction, self.lang["setting_flag_msg"], True)
            return

        # Verify if the specified Twitter user exists using the Twitter client.
        # Twitterクライアントを使用して、指定されたTwitterユーザーが存在するかどうかを確認します。
        if not await self.bot.twitter_client.user_exist(twitter_user_name):
            await self.message_send(interaction, self.lang["unknown_user_msg"], True)
            return

        # 新設計: guild_twitter_feedsに登録
        self.bot.db.cursor.execute('''
            INSERT OR IGNORE INTO guild_twitter_feeds (guild_id, channel_id, twitter_user_name, created_at)
            VALUES (?, ?, ?, ?)
        ''', (guild_id, channel_id, twitter_user_name, int(time.time())))
        self.bot.db.conn.commit()
        # 新設計: global_twitter_usersに存在しなければ空データで追加
        if not self.bot.db.get_global_twitter_user(twitter_user_name):
            self.bot.db.cursor.execute('''
                INSERT OR IGNORE INTO global_twitter_users (twitter_user_name, last_tweet_id, last_tweet_url, second_last_tweet_id, second_last_tweet_url, last_updated)
                VALUES (?, NULL, NULL, NULL, NULL, 0)
            ''', (twitter_user_name,))
            self.bot.db.conn.commit()
        # 既存のadd_twitter_feedも後方互換で呼ぶ
        success = self.bot.db.add_twitter_feed(guild_id, channel_id, twitter_user_name)
        if not success:
            await self.message_send(interaction, self.lang["duplicated_user_msg"], True)
            return
        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='del_twitter')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def del_command(self, interaction: discord.Interaction, user_name: str):
        """
        Remove a Twitter feed from a channel.
        This command allows administrators to stop tracking a specific Twitter user in a channel.

        Args:
            interaction: The interaction object from Discord.
            user_name (str): The Twitter username to unfollow.

        チャンネルからTwitterフィードを削除します。
        このコマンドは、管理者がチャンネルで特定のTwitterユーザーの追跡を停止することを可能にします。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            user_name (str): フォローを解除するTwitterユーザー名。
        """
        # Get channel and guild IDs from the interaction.
        # インタラクションからチャンネルIDとギルドIDを取得します。
        channel_id = interaction.channel_id
        guild_id = interaction.guild_id

        # Attempt to remove the feed from the database.
        # データベースからフィードを削除しようとします。
        # 新設計: guild_twitter_feedsから削除
        self.bot.db.cursor.execute('''
            DELETE FROM guild_twitter_feeds 
            WHERE guild_id = ? AND channel_id = ? AND twitter_user_name = ?
        ''', (guild_id, channel_id, user_name))
        self.bot.db.conn.commit()
        # 既存のremove_twitter_feedも後方互換で呼ぶ
        success = self.bot.db.remove_twitter_feed(channel_id, user_name)
        if success:
            await self.message_send(interaction, self.lang["setting_completed_msg"], True)
        else:
            # If the feed was not found in the database, inform the user.
            # データベースにフィードが見つからなかった場合、ユーザーに通知します。
            await self.message_send(interaction, self.lang["no_user_registration_msg"], True)

    def get_minimum_cooldown(self) -> int:
        """
        Get the minimum cooldown time across all guilds.
        If no guilds are found or no cooldown settings are set, returns a default value of 5 minutes.

        Returns:
            int: The minimum cooldown time in minutes.

        すべてのギルドの最小クールダウン時間を取得します。
        ギルドが見つからないか、クールダウン設定が設定されていない場合は、デフォルト値の5分を返します。

        Returns:
            int: 分単位の最小クールダウン時間。
        """
        try:
            # Get all guild IDs from the database
            guild_ids = self.bot.db.get_all_guild_ids()

            if not guild_ids:
                logger.info("No guilds found, using default cooldown of 5 minutes")
                return 5  # Default to 5 minutes if no guilds are found

            min_cooldown = float('inf')  # Start with infinity

            for guild_id in guild_ids:
                # Get guild settings
                guild_settings = self.bot.db.get_guild_settings(guild_id)

                # Skip if Twitter updates are disabled for this guild or settings don't exist
                if not guild_settings or not guild_settings['twitter_updates_enabled']:
                    continue

                # Update min_cooldown if this guild has a lower value
                if guild_settings['cool_down_minutes'] < min_cooldown:
                    min_cooldown = guild_settings['cool_down_minutes']

            # If no enabled guilds were found, return default
            if min_cooldown == float('inf'):
                logger.info("No enabled guilds found, using default cooldown of 5 minutes")
                return 5

            result = max(1, min_cooldown)  # Ensure at least 1 minute
            logger.info(f"Minimum cooldown across all guilds: {result} minutes")
            return result
        except Exception as e:
            logger.error(f"Error getting minimum cooldown: {e}", exc_info=e)
            return 5  # Default to 5 minutes on error

    def update_check_interval(self) -> None:
        """
        Update the loop task interval based on the minimum cooldown time across all guilds.
        If the task is already running, it will be restarted with the new interval.

        すべてのギルドの最小クールダウン時間に基づいて、loopタスクの間隔を更新します。
        タスクがすでに実行されている場合は、新しい間隔で再起動されます。
        """
        # Get the minimum cooldown time
        min_cooldown = self.get_minimum_cooldown()

        # If the task is already running, cancel it
        if self.loop.is_running():
            logger.info("Cancelling existing Twitter update loop")
            self.loop.cancel()

        # Change the interval and restart the task
        self.loop.change_interval(seconds=60)
        self.loop.start()

        logger.info(f"Twitter update loop interval set to 60 seconds")

    @app_commands.command(name='check-time')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def cool_down(self, interaction: discord.Interaction, minutes: int):
        """
        Set the cool down time (in minutes) for Twitter updates for the current guild.
        This prevents the bot from checking for updates too frequently.

        Args:
            interaction: The interaction object from Discord.
            minutes (int): The cool down time in minutes. Must be at least 1.

        現在のギルドのTwitter更新のクールダウン時間（分）を設定します。
        これにより、ボットが頻繁に更新をチェックするのを防ぎます。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            minutes (int): クールダウン時間（分）。1以上である必要があります。
        """
        # Ensure minutes is at least 1 to prevent invalid cool-down times.
        # 無効なクールダウン時間を防ぐため、分が1以上であることを確認します。
        minutes = max(1, minutes)

        # Update the cool-down setting for the guild in the database.
        # データベースでギルドのクールダウン設定を更新します。
        self.bot.db.update_guild_settings(interaction.guild_id, cool_down_minutes=minutes)

        # Update the check interval based on the new cooldown setting
        # 新しいクールダウン設定に基づいてチェック間隔を更新します
        self.update_check_interval()

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='change-setting-twitter-get')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def change_setting_twitter_get(self, interaction: discord.Interaction, mode: bool):
        """
        Enable or disable Twitter updates for the current guild.
        This controls whether the bot will fetch and post Twitter updates for any feeds in this guild.

        Args:
            interaction: The interaction object from Discord.
            mode (bool): True to enable Twitter updates, False to disable.

        現在のギルドのTwitter更新を有効または無効にします。
        これは、ボットがこのギルドのフィードのTwitter更新を取得して投稿するかどうかを制御します。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            mode (bool): Twitter更新を有効にする場合はTrue、無効にする場合はFalse。
        """
        # Get guild ID from the interaction.
        # インタラクションからギルドIDを取得します。
        guild_id = interaction.guild_id

        # Update the twitter_updates_enabled setting in the database.
        # データベースでtwitter_updates_enabled設定を更新します。
        self.bot.db.update_guild_settings(guild_id, twitter_updates_enabled=mode)

        # Update the check interval as enabling/disabling updates can affect the minimum cooldown
        # 更新の有効化/無効化が最小クールダウンに影響する可能性があるため、チェック間隔を更新します
        self.update_check_interval()

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='change-setting-url-preview')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def change_setting_url_preview(self, interaction: discord.Interaction, mode: bool):
        """
        Enable or disable URL previews (fxtwitter.com conversion) for the current guild.
        When enabled, Twitter/X.com URLs will be converted to fxtwitter.com links for better embedding.

        Args:
            interaction: The interaction object from Discord.
            mode (bool): True to enable URL previews, False to disable.

        現在のギルドのURLプレビュー（fxtwitter.com変換）を有効または無効にします。
        有効にすると、Twitter/X.comのURLはより良い埋め込みのためにfxtwitter.comのリンクに変換されます。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            mode (bool): URLプレビューを有効にする場合はTrue、無効にする場合はFalse。
        """
        # Get guild ID from the interaction.
        # インタラクションからギルドIDを取得します。
        guild_id = interaction.guild_id

        # Update the url_preview_enabled setting in the database.
        # データベースでurl_preview_enabled設定を更新します。
        self.bot.db.update_guild_settings(guild_id, url_preview_enabled=mode)

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='set-tweet-filter')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_tweet_filter(self, interaction: discord.Interaction, filter_type: str):
        """
        Set the type of tweets to post for the current guild.
        This controls which types of tweets (original, retweet, reply) will be posted to Discord channels.

        Args:
            interaction: The interaction object from Discord.
            filter_type (str): The type of tweets to post. Options: 'original', 'retweet', 'reply', 'original,retweet', 'original,reply', 'retweet,reply', 'all'

        現在のギルドに投稿するツイートのタイプを設定します。
        これは、どのタイプのツイート（オリジナル、リツイート、返信）がDiscordチャンネルに投稿されるかを制御します。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            filter_type (str): 投稿するツイートのタイプ。オプション: 'original', 'retweet', 'reply', 'original,retweet', 'original,reply', 'retweet,reply', 'all'
        """
        # Get guild ID from the interaction.
        # インタラクションからギルドIDを取得します。
        guild_id = interaction.guild_id

        # Validate the filter_type
        valid_types = ['original', 'retweet', 'reply', 'original,retweet', 'original,reply', 'retweet,reply', 'all']
        if filter_type not in valid_types:
            await self.message_send(interaction, f"Invalid filter type. Valid options are: {', '.join(valid_types)}", True)
            return

        # Update the tweet_type_filter setting in the database.
        # データベースでtweet_type_filter設定を更新します。
        self.bot.db.update_guild_settings(guild_id, tweet_type_filter=filter_type)

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='check-settings')
    async def check_setting(self, interaction: discord.Interaction):
        """
        Display the current settings and configured Twitter feeds for the guild.
        This command provides an overview of the bot's configuration for the guild.

        Args:
            interaction: The interaction object from Discord.

        ギルドの現在の設定と設定済みのTwitterフィードを表示します。
        このコマンドは、ギルドのボット設定の概要を提供します。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
        """
        # Get guild ID from the interaction.
        # インタラクションからギルドIDを取得します。
        guild_id = interaction.guild_id

        # Retrieve guild settings from the database.
        # データベースからギルド設定を取得します。
        guild_settings = self.bot.db.get_guild_settings(guild_id)

        # If no settings exist, create default settings and then retrieve them.
        # 設定が存在しない場合、デフォルト設定を作成してから取得します。
        if guild_settings is None:
            self.bot.db.update_guild_settings(
                guild_id,
                twitter_updates_enabled=True,
                url_preview_enabled=True,
                cool_down_minutes=1
            )
            guild_settings = self.bot.db.get_guild_settings(guild_id)

        # 新設計: guild_twitter_feedsからも取得
        self.bot.db.cursor.execute('''
            SELECT channel_id, twitter_user_name FROM guild_twitter_feeds 
            WHERE guild_id = ?
        ''', (guild_id,))
        new_feeds = self.bot.db.cursor.fetchall()
        # 既存のget_twitter_feedsも後方互換で呼ぶ
        feeds = self.bot.db.get_twitter_feeds(guild_id)
        # 新設計のフィードを優先、既存フィードで補完
        if new_feeds:
            setting_channels = [feed['channel_id'] for feed in new_feeds]
            twitter_user_names = [feed['twitter_user_name'] for feed in new_feeds]
        else:
            setting_channels = [feed['channel_id'] for feed in feeds]
            twitter_user_names = [feed['twitter_user_name'] for feed in feeds]

        # Extract individual settings for display.
        # 表示用に個々の設定を抽出します。
        cool_down_time = guild_settings['cool_down_minutes']
        twitter_updates_enabled = guild_settings['twitter_updates_enabled']
        url_preview_enabled = guild_settings['url_preview_enabled']
        tweet_type_filter = guild_settings.get('tweet_type_filter', 'original')

        # Create a Discord embed to display the settings.
        # 設定を表示するためのDiscord埋め込みを作成します。
        embed = discord.Embed(
            title=self.lang["embed_setting"],
            description=f"{self.lang['embed_check_time']} : {cool_down_time}{self.lang['embed_minutes']}\n"
                       f"{self.lang['embed_new_tweet']} : {twitter_updates_enabled}\n"
                       f"{self.lang['embed_change_fxtwitter']}：{url_preview_enabled}\n"
                       f"Tweet Type Filter : {tweet_type_filter}",
            color=0x219900
        )

        # Initialize strings to hold lists of channels and Twitter users.
        # チャンネルとTwitterユーザーのリストを保持する文字列を初期化します。
        channel_string = ""
        twitter_user_names_string = ""
        message_count = 0
        # message_flag: True if a followup message has been sent, False otherwise.
        # This helps determine whether to use interaction.response.send_message or interaction.followup.send.
        # message_flag: フォローアップメッセージが送信された場合はTrue、それ以外の場合はFalse。
        # これにより、interaction.response.send_messageとinteraction.followup.sendのどちらを使用するかを判断します。
        message_flag = False

        # Iterate through configured feeds to add them to the embed.
        # 設定されたフィードを反復処理して、埋め込みに追加します。
        for setting_channel, twitter_user_name in zip(setting_channels, twitter_user_names):
            # Estimate message length to avoid Discord embed limits (1024 characters per field).
            # Each channel ID is a number, and a Twitter username can vary in length.
            # Discordの埋め込み制限（フィールドあたり1024文字）を避けるために、メッセージの長さを推定します。
            # 各チャンネルIDは数値であり、Twitterユーザー名は長さが異なります。
            message_count += 4 + len(str(setting_channel)) + 18 + len(twitter_user_name)

            # If adding the next item would exceed the limit, send the current embed and start a new one.
            # 次の項目を追加すると制限を超える場合、現在の埋め込みを送信し、新しい埋め込みを開始します。
            if message_count >= 1024:
                embed.add_field(name=self.lang["embed_setting_channel"], value=channel_string or "None", inline=True)
                embed.add_field(name=self.lang["embed_setting_user"], value=twitter_user_names_string or "None", inline=True)

                # Use followup.send for subsequent embeds after the initial response.
                # 最初の応答後の後続の埋め込みにはfollowup.sendを使用します。
                if message_flag:
                    await interaction.followup.send(embed=embed)
                else:
                    # The first embed should use response.send_message.
                    # 最初の埋め込みはresponse.send_messageを使用する必要があります。
                    await interaction.response.send_message(embed=embed)

                # Reset for a new embed.
                # 新しい埋め込みのためにリセットします。
                embed = discord.Embed(title=self.lang["embed_setting_channel"], color=0x219900)
                message_count = 0
                channel_string = ""
                twitter_user_names_string = ""
                # Set flag to True as subsequent sends will be followups.
                # 以降の送信はフォローアップになるため、フラグをTrueに設定します。
                message_flag = True

            # Append the channel and Twitter user to their respective strings.
            # チャンネルとTwitterユーザーをそれぞれの文字列に追加します。
            channel_string += f"<#{setting_channel}>\n"
            twitter_user_names_string += f"[{twitter_user_name}](https://x.com/{twitter_user_name})\n"

        # Add any remaining channels and Twitter users to the embed.
        # 残りのチャンネルとTwitterユーザーを埋め込みに追加します。
        embed.add_field(name=self.lang["embed_setting_channel"], value=channel_string or "None", inline=True)
        embed.add_field(name=self.lang["embed_setting_user"], value=twitter_user_names_string or "None", inline=True)

        # Send the final embed. Use followup if previous embeds were sent, otherwise use initial response.
        # 最終的な埋め込みを送信します。以前に埋め込みが送信された場合はfollowupを使用し、それ以外の場合は最初の応答を使用します。
        if message_flag:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name='test-tweet')
    async def test_tweet(self, interaction: discord.Interaction, url: str):
        """
        Test the expansion of a Twitter/X URL.
        This command allows users to check if a Twitter/X URL can be properly expanded.

        Args:
            interaction: The interaction object from Discord.
            url (str): The Twitter/X URL to test (e.g., "https://x.com/username/status/123456789").

        Twitter/X URLの展開をテストします。
        このコマンドは、Twitter/X URLが適切に展開できるかどうかをユーザーが確認することを可能にします。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            url (str): テストするTwitter/X URL（例: "https://x.com/username/status/123456789"）。
        """
        # Check if the URL is a Twitter/X URL
        if not ("https://twitter.com" in url or "https://x.com" in url):
            await self.message_send(interaction, self.lang["test_tweet_invalid_url"], True)
            return

        # Inform the user that we're processing their request
        await interaction.response.defer(ephemeral=True)

        # Convert to fxtwitter URL for better embedding
        if "https://twitter.com" in url:
            fx_url = url.replace("https://twitter.com", "https://fxtwitter.com")
        else:
            fx_url = url.replace("https://x.com", "https://fxtwitter.com")

        # Create an embed to display the results
        embed = discord.Embed(
            title=self.lang["test_tweet_title"],
            description=f"Original URL: {url}\nConverted URL: {fx_url}",
            color=0x1DA1F2  # Twitter blue color
        )

        # Send the results
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Also send the converted URL for preview
        await interaction.followup.send(fx_url)

    @app_commands.command(name='test-latest-tweets')
    async def test_latest_tweets(self, interaction: discord.Interaction, twitter_user_name: str, count: int = 5):
        """
        Test command to fetch and display the latest tweets from a specific Twitter user.
        This command is useful for testing the Twitter API connection and tweet fetching functionality.

        Args:
            interaction: The interaction object from Discord.
            twitter_user_name (str): The Twitter username (without @) to fetch tweets from.
            count (int, optional): Number of latest tweets to fetch (default: 5, max: 20).

        Twitterユーザーの最新ツイートを取得して表示するテストコマンドです。
        このコマンドは、Twitter API接続とツイート取得機能のテストに役立ちます。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            twitter_user_name (str): ツイートを取得するTwitterユーザー名（@なし）。
            count (int, optional): 取得する最新ツイートの数（デフォルト: 5、最大: 20）。
        """
        # Validate count parameter
        if count < 1 or count > 20:
            await self.message_send(interaction, self.lang.get("test_latest_tweets_invalid_count", "Count must be between 1 and 20."), True)
            return

        # Inform the user that we're processing their request
        await interaction.response.defer(ephemeral=True)

        try:
            # Fetch the latest tweets
            tweets = await get_latest_tweets_with_manager(
                self.bot.twitter_client_manager,
                screen_name=twitter_user_name,
                count=count
            )

            if not tweets:
                await interaction.followup.send(
                    self.lang.get("test_latest_tweets_no_tweets", "No tweets found for @{0}").format(twitter_user_name),
                    ephemeral=True
                )
                return

            # Create an embed to display the results
            embed = discord.Embed(
                title=self.lang.get("test_latest_tweets_title", "Latest Tweets Test Results"),
                description=self.lang.get("test_latest_tweets_description", "Latest {0} tweets from @{1}").format(len(tweets), twitter_user_name),
                color=0x1DA1F2  # Twitter blue color
            )

            # Add each tweet to the embed
            for i, tweet in enumerate(tweets, 1):
                # Truncate tweet text if it's too long
                tweet_text = tweet.text[:200] + "..." if len(tweet.text) > 200 else tweet.text
                
                # Create field name with tweet number and date
                field_name = f"{i}. Tweet by @{tweet.author.screen_name}"
                
                # Create field value with tweet content and metadata
                field_value = f"**Content:** {tweet_text}\n"
                field_value += f"**Date:** {tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                field_value += f"**Likes:** {tweet.likes}\n"
                field_value += f"**Retweets:** {tweet.retweets}\n"
                field_value += f"**Replies:** {tweet.replies}\n"
                
                # Add tweet URL if available
                if hasattr(tweet, 'url') and tweet.url:
                    field_value += f"**URL:** {tweet.url}\n"
                
                # Add field to embed (Discord has a limit of 1024 characters per field)
                if len(field_value) > 1024:
                    field_value = field_value[:1021] + "..."
                
                embed.add_field(name=field_name, value=field_value, inline=False)

            # Add footer with additional information
            embed.set_footer(text=self.lang.get("test_latest_tweets_footer", "Test completed successfully"))

            # Send the results
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Log the test
            logger.info(f"Test latest tweets completed for @{twitter_user_name}: {len(tweets)} tweets fetched")

        except Exception as e:
            error_msg = self.lang.get("test_latest_tweets_error", "Error fetching tweets for @{0}: {1}").format(twitter_user_name, str(e))
            await interaction.followup.send(error_msg, ephemeral=True)
            logger.error(f"Error in test_latest_tweets for @{twitter_user_name}: {e}", exc_info=True)

    @app_commands.command(name='test-current-urls')
    async def test_current_urls(self, interaction: discord.Interaction, target_type: str = "all", target_id: str = None):
        """
        Test command to fetch and display current URLs from the database.
        This command is useful for testing the database URL retrieval functionality.

        Args:
            interaction: The interaction object from Discord.
            target_type (str): Type of target to get URLs for ("all", "user", "guild", "channel").
            target_id (str, optional): Target ID (username for user, guild ID for guild, channel ID for channel).

        SQLデータベースから現在のURLを取得して表示するテストコマンドです。
        このコマンドは、データベースURL取得機能のテストに役立ちます。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            target_type (str): URLを取得するターゲットのタイプ（"all", "user", "guild", "channel"）。
            target_id (str, optional): ターゲットID（ユーザーの場合はユーザー名、ギルドの場合はギルドID、チャンネルの場合はチャンネルID）。
        """
        # Validate target_type parameter
        valid_types = ["all", "user", "guild", "channel"]
        if target_type not in valid_types:
            await self.message_send(interaction, f"Invalid target_type. Must be one of: {', '.join(valid_types)}", True)
            return

        # Check if target_id is required but not provided
        if target_type != "all" and not target_id:
            await self.message_send(interaction, f"target_id is required for target_type '{target_type}'", True)
            return

        # Inform the user that we're processing their request
        await interaction.response.defer(ephemeral=True)

        try:
            urls_data = []
            
            if target_type == "all":
                urls_data = self.bot.db.get_all_current_urls()
            elif target_type == "user":
                user_data = self.bot.db.get_current_urls_for_user(target_id)
                if user_data:
                    urls_data = [{'twitter_user_name': target_id, **user_data}]
            elif target_type == "guild":
                try:
                    guild_id = int(target_id)
                    urls_data = self.bot.db.get_urls_by_guild(guild_id)
                except ValueError:
                    await interaction.followup.send("Invalid guild ID. Must be a number.", ephemeral=True)
                    return
            elif target_type == "channel":
                try:
                    channel_id = int(target_id)
                    urls_data = self.bot.db.get_urls_by_channel(channel_id)
                except ValueError:
                    await interaction.followup.send("Invalid channel ID. Must be a number.", ephemeral=True)
                    return

            if not urls_data:
                await interaction.followup.send(
                    self.lang.get("test_current_urls_no_data", "No URL data found for the specified target."),
                    ephemeral=True
                )
                return

            # Create an embed to display the results
            embed = discord.Embed(
                title=self.lang.get("test_current_urls_title", "Current URLs Test Results"),
                description=self.lang.get("test_current_urls_description", "Found {0} URL records").format(len(urls_data)),
                color=0x1DA1F2  # Twitter blue color
            )

            # Add each URL record to the embed
            for i, data in enumerate(urls_data[:10], 1):  # Limit to first 10 results
                # Create field name
                field_name = f"{i}. @{data['twitter_user_name']}"
                
                # Create field value with URL information
                field_value = ""
                
                if data.get('last_tweet_url'):
                    field_value += f"**Latest Tweet:** {data['last_tweet_url']}\n"
                
                if data.get('second_last_tweet_url'):
                    field_value += f"**Second Latest:** {data['second_last_tweet_url']}\n"
                
                if data.get('last_updated'):
                    from datetime import datetime
                    last_updated = datetime.fromtimestamp(data['last_updated'])
                    field_value += f"**Last Updated:** {last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                # Add additional context based on target_type
                if target_type == "guild" and data.get('channel_id'):
                    field_value += f"**Channel:** <#{data['channel_id']}>\n"
                elif target_type == "channel" and data.get('guild_id'):
                    field_value += f"**Guild ID:** {data['guild_id']}\n"
                
                # Add field to embed (Discord has a limit of 1024 characters per field)
                if len(field_value) > 1024:
                    field_value = field_value[:1021] + "..."
                
                embed.add_field(name=field_name, value=field_value, inline=False)

            # Add footer with additional information
            if len(urls_data) > 10:
                embed.set_footer(text=self.lang.get("test_current_urls_footer_more", "Showing first 10 of {0} results").format(len(urls_data)))
            else:
                embed.set_footer(text=self.lang.get("test_current_urls_footer", "Test completed successfully"))

            # Send the results
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Log the test
            logger.info(f"Test current URLs completed for {target_type}: {len(urls_data)} records found")

        except Exception as e:
            error_msg = self.lang.get("test_current_urls_error", "Error fetching URLs: {0}").format(str(e))
            await interaction.followup.send(error_msg, ephemeral=True)
            logger.error(f"Error in test_current_urls for {target_type}: {e}", exc_info=True)

    @app_commands.command(name='test-new-structure')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def test_new_structure(self, interaction: discord.Interaction):
        """
        Test the new structure (global_twitter_users and guild_twitter_feeds).
        This command shows the current state of the new database structure.
        """
        guild_id = interaction.guild_id
        
        # Get data from new structure
        self.bot.db.cursor.execute("SELECT COUNT(*) FROM global_twitter_users")
        global_users_count = self.bot.db.cursor.fetchone()[0]
        
        self.bot.db.cursor.execute("SELECT COUNT(*) FROM guild_twitter_feeds")
        guild_feeds_count = self.bot.db.cursor.fetchone()[0]
        
        # Get guild-specific data
        self.bot.db.cursor.execute('''
            SELECT channel_id, twitter_user_name FROM guild_twitter_feeds 
            WHERE guild_id = ?
        ''', (guild_id,))
        guild_feeds = self.bot.db.cursor.fetchall()
        
        # Get global users
        self.bot.db.cursor.execute('SELECT twitter_user_name FROM global_twitter_users')
        global_users = [row['twitter_user_name'] for row in self.bot.db.cursor.fetchall()]
        
        embed = discord.Embed(
            title="New Structure Test Results",
            description=f"Global Users: {global_users_count}\nGuild Feeds: {guild_feeds_count}",
            color=0x1DA1F2
        )
        
        if guild_feeds:
            feeds_text = "\n".join([f"<#{feed['channel_id']}> -> @{feed['twitter_user_name']}" for feed in guild_feeds])
            embed.add_field(name="Guild Feeds", value=feeds_text, inline=False)
        
        if global_users:
            users_text = "\n".join([f"@{user}" for user in global_users[:10]])  # Show first 10
            if len(global_users) > 10:
                users_text += f"\n... and {len(global_users) - 10} more"
            embed.add_field(name="Global Users", value=users_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

