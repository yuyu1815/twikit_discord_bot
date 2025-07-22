import discord
import time
import os
from discord import app_commands
from discord.ext import commands, tasks
from pathlib import Path

from src.rss.rss_generator import RSSGenerator
from src.core.twitter_analyzer import get_rss_like_tweets_with_manager, analyze_tweet_with_manager

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
        # Dictionary to track the last RSS update time for each Twitter user
        # 各Twitterユーザーの最後のRSS更新時間を追跡する辞書
        self.last_rss_update_times = {}

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
        print(self.lang.get("twitter_commands_message_log", "{0}").format(msg))
        await interaction.response.send_message(msg, ephemeral=ephemeral)

    @tasks.loop(seconds=10)
    async def loop(self):
        """
        Periodically check for new tweets from registered Twitter users and post them to the designated Discord channels.
        This matches the implementation from src_old/Bot.py.

        登録されたTwitterユーザーの新しいツイートを定期的にチェックし、指定されたDiscordチャンネルに投稿します。
        これはsrc_old/Bot.pyの実装と一致します。
        """
        now_time = time.time()
        guild_ids = self.bot.db.get_all_guild_ids()
        if guild_ids is None:
            return
        for guild_id in guild_ids:
            guild_settings = self.bot.db.get_guild_settings(guild_id)
            if guild_settings is None or not guild_settings.get('twitter_updates_enabled', False):
                continue

            # Check cooldown per guild
            if int(guild_settings['cool_down_minutes']) * 60 > now_time - guild_settings.get('last_checked_time', 0):
                continue

            # Update last checked time for the entire guild
            self.bot.db.update_guild_settings(guild_id, last_checked_time=int(time.time()))

            # Get all Twitter feeds for this guild and process them
            feeds = self.bot.db.get_twitter_feeds(guild_id)
            for feed in feeds:
                await self._process_twitter_feed(guild_id, feed, guild_settings)

    @loop.before_loop
    async def before_loop(self):
        """
        Wait until the bot is ready before starting the loop task.

        loopタスクを開始する前に、ボットの準備が整うまで待ちます。
        """
        await self.bot.wait_until_ready()

    async def _process_twitter_feed(self, guild_id, feed, guild_settings):
        """
        Process a single Twitter feed, checking for new tweets and posting them to the designated Discord channel.

        Args:
            guild_id (int): The ID of the Discord guild.
            feed (dict): The Twitter feed information from the database.
            guild_settings (dict): The guild settings from the database.

        単一のTwitterフィードを処理し、新しいツイートをチェックして指定されたDiscordチャンネルに投稿します。

        Args:
            guild_id (int): DiscordギルドのID。
            feed (dict): データベースからのTwitterフィード情報。
            guild_settings (dict): データベースからのギルド設定。
        """
        try:
            channel_id = feed['channel_id']
            twitter_user_name = feed['twitter_user_name']

            # Get the channel object
            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"Channel {channel_id} not found for Twitter feed {twitter_user_name}")
                return

            # Get tweet history for this feed
            tweet_history = self.bot.db.get_tweet_history(channel_id, twitter_user_name)
            last_tweet_id = tweet_history[0] if tweet_history and tweet_history[0] is not None else 0

            # Fetch the latest tweets for the user
            tweets = await get_rss_like_tweets_with_manager(
                self.bot.twitter_client_manager,
                screen_name=twitter_user_name,
                count=10
            )

            if not tweets:
                return  # No tweets found

            # Filter out tweets that are older than the last tweet we've seen
            new_tweets = []
            for tweet in tweets:
                if last_tweet_id == 0 or int(tweet.id) > int(last_tweet_id):
                    new_tweets.append(tweet)

            if not new_tweets:
                return  # No new tweets

            # Sort tweets by ID (oldest first)
            new_tweets.sort(key=lambda t: int(t.id))

            # Get the tweet type filter setting
            tweet_type_filter = guild_settings.get('tweet_type_filter', 'original')
            tweet_types = tweet_type_filter.split(',')

            # Track the most recent tweet ID processed in this batch
            most_recent_tweet_id = None

            # Process each new tweet
            for tweet in new_tweets:
                # Analyze the tweet to determine its type
                analysis = await analyze_tweet_with_manager(self.bot.twitter_client_manager, tweet.id)
                tweet_type = analysis.get('type', 'unknown')

                # Skip tweets that don't match the filter
                if tweet_type not in tweet_types and 'all' not in tweet_types:
                    continue

                # Create and send an embed for the tweet
                await self._send_tweet_embed(channel, tweet, analysis)

                # Update the most recent tweet ID
                most_recent_tweet_id = tweet.id

            # After processing all tweets, update the database with the most recent tweet ID
            if most_recent_tweet_id:
                if tweet_history:
                    self.bot.db.update_tweet_history(
                        channel_id, 
                        twitter_user_name, 
                        most_recent_tweet_id, 
                        last_tweet_id
                    )
                else:
                    # If there's no history yet, create a new entry
                    self.bot.db.update_tweet_history(
                        channel_id, 
                        twitter_user_name, 
                        most_recent_tweet_id, 
                        0
                    )

        except Exception as e:
            print(f"Error processing Twitter feed {feed['twitter_user_name']} for guild {guild_id}: {e}")

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
            print(f"Error sending tweet embed: {e}")

    @app_commands.command(name='set_twitter')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_command(self, interaction: discord.Interaction, twitter_user_name: str):
        """
        Set up a Twitter feed for the current channel.
        This command allows administrators to specify a Twitter username to track.

        Args:
            interaction: The interaction object from Discord.
            twitter_user_name (str): The Twitter username to follow for updates.

        現在のチャンネルにTwitterフィードを設定します。
        このコマンドは、管理者が追跡するTwitterユーザー名を指定することを可能にします。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            twitter_user_name (str): 更新をフォローするTwitterユーザー名。
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

        # Attempt to add the Twitter feed to the database.
        # Twitterフィードをデータベースに追加しようとします。
        success = self.bot.db.add_twitter_feed(guild_id, channel_id, twitter_user_name)

        # If the feed already exists (due to UNIQUE constraint), inform the user.
        # フィードが既に存在する場合（UNIQUE制約のため）、ユーザーに通知します。
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
        success = self.bot.db.remove_twitter_feed(channel_id, user_name)

        if success:
            await self.message_send(interaction, self.lang["setting_completed_msg"], True)
        else:
            # If the feed was not found in the database, inform the user.
            # データベースにフィードが見つからなかった場合、ユーザーに通知します。
            await self.message_send(interaction, self.lang["no_user_registration_msg"], True)

    def get_minimum_cooldown(self):
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
                return 5

            return max(1, min_cooldown)  # Ensure at least 1 minute
        except Exception as e:
            print(f"Error getting minimum cooldown: {e}")
            return 5  # Default to 5 minutes on error

    def update_check_interval(self):
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
            self.loop.cancel()

        # Change the interval and restart the task
        self.loop.change_interval(seconds=10)
        self.loop.start()

        print(f"Twitter update loop interval set to 10 seconds")

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

        # Retrieve all Twitter feeds configured for this guild.
        # このギルドに設定されているすべてのTwitterフィードを取得します。
        feeds = self.bot.db.get_twitter_feeds(guild_id)

        # Extract channel IDs and Twitter usernames from the feeds.
        # フィードからチャンネルIDとTwitterユーザー名を抽出します。
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

    @app_commands.command(name='generate_rss')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def generate_rss(self, interaction: discord.Interaction, twitter_user_name: str):
        """
        Generate an RSS feed for a Twitter user.
        This command creates or updates an RSS XML file containing the latest tweets from the specified user.

        Args:
            interaction: The interaction object from Discord.
            twitter_user_name (str): The Twitter username to generate an RSS feed for.

        Twitterユーザーの最新ツイートを含むRSSフィードを生成します。
        このコマンドは、指定されたユーザーの最新ツイートを含むRSS XMLファイルを作成または更新します。

        Args:
            interaction: Discordからのインタラクションオブジェクト。
            twitter_user_name (str): RSSフィードを生成するTwitterユーザー名。
        """
        # Verify if the specified Twitter user exists
        # 指定されたTwitterユーザーが存在するかどうかを確認します
        if not await self.bot.twitter_client.user_exist(twitter_user_name):
            await self.message_send(interaction, self.lang["unknown_user_msg"], True)
            return

        # Inform the user that we're processing their request
        # リクエストを処理していることをユーザーに通知します
        await interaction.response.defer(ephemeral=True)

        # Check if the user is in cooldown period
        # ユーザーがクールダウン期間中かどうかを確認します
        now_time = time.time()
        last_update_time = self.last_rss_update_times.get(twitter_user_name, 0)
        cooldown_seconds = self.bot.settings.rss_feed_cooldown_minutes * 60

        # Create the RSS output directory if it doesn't exist
        # RSS出力ディレクトリが存在しない場合は作成します
        rss_output_dir = self.bot.settings.rss_feed_output_dir
        os.makedirs(rss_output_dir, exist_ok=True)

        # Check if an RSS file already exists for this user
        # このユーザーのRSSファイルが既に存在するかどうかを確認します
        rss_file_path = Path(rss_output_dir) / f"{twitter_user_name}.xml"
        file_exists = rss_file_path.exists()

        # If in cooldown and file exists, return the existing file
        # クールダウン中でファイルが存在する場合、既存のファイルを返します
        if file_exists and (now_time - last_update_time) < cooldown_seconds:
            cooldown_remaining = int((last_update_time + cooldown_seconds - now_time) / 60) + 1
            await interaction.followup.send(
                f"{self.lang.get('rss_cooldown_message', 'RSS feed for {0} was updated recently. Please try again in {1} minutes.').format(twitter_user_name, cooldown_remaining)}\n"
                f"{self.lang.get('rss_existing_file', 'Using existing RSS file:')} {rss_file_path}",
                ephemeral=True
            )
            return

        try:
            # Get tweets using the Twitter client manager
            # Twitterクライアントマネージャーを使用してツイートを取得します
            tweets = await get_rss_like_tweets_with_manager(
                self.bot.twitter_client_manager,
                screen_name=twitter_user_name,
                count=self.bot.settings.rss_feed_max_tweets
            )

            if not tweets:
                await interaction.followup.send(
                    self.lang.get('rss_no_tweets', 'No tweets found for {0}.').format(twitter_user_name),
                    ephemeral=True
                )
                return

            # Generate RSS feed
            # RSSフィードを生成します
            rss_generator = RSSGenerator(
                output_dir=str(rss_output_dir),
                max_tweets=self.bot.settings.rss_feed_max_tweets
            )

            # Save RSS feed to file
            # RSSフィードをファイルに保存します
            file_path = rss_generator.save_rss(tweets, twitter_user_name)

            # Update the last update time for this user
            # このユーザーの最終更新時間を更新します
            self.last_rss_update_times[twitter_user_name] = now_time

            # Send success message with file path
            # ファイルパスを含む成功メッセージを送信します
            await interaction.followup.send(
                self.lang.get('rss_generation_success', 'RSS feed for {0} generated successfully.').format(twitter_user_name) + 
                f"\n{self.lang.get('rss_file_path', 'File path:')} {file_path}",
                ephemeral=True
            )

        except Exception as e:
            # Handle errors
            # エラーを処理します
            error_message = str(e)
            await interaction.followup.send(
                self.lang.get('rss_generation_error', 'Error generating RSS feed: {0}').format(error_message),
                ephemeral=True
            )
