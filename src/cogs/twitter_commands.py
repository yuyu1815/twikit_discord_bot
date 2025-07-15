import discord
from discord import app_commands
from discord.ext import commands

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
        print(msg)
        await interaction.response.send_message(msg, ephemeral=ephemeral)

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

        # Create a Discord embed to display the settings.
        # 設定を表示するためのDiscord埋め込みを作成します。
        embed = discord.Embed(
            title=self.lang["embed_setting"],
            description=f"{self.lang['embed_check_time']} : {cool_down_time}{self.lang['embed_minutes']}\n"
                       f"{self.lang['embed_new_tweet']} : {twitter_updates_enabled}\n"
                       f"{self.lang['embed_change_fxtwitter']}：{url_preview_enabled}",
            color=0x219900
        )

        # Initialize strings to hold lists of channels and Twitter users.
        # チャンネルとTwitterユーザーのリストを保持する文字列を初期化します。
        channel_string = ""
        twitter_user_names_string = ""
        message_count = 0
        message_flag = False # Flag to track if followup.send is needed

        # Iterate through configured feeds to add them to the embed.
        # 設定されたフィードを反復処理して、埋め込みに追加します。
        for setting_channel, twitter_user_name in zip(setting_channels, twitter_user_names):
            # Estimate message length to avoid Discord embed limits (1024 characters per field).
            # Discordの埋め込み制限（フィールドあたり1024文字）を避けるために、メッセージの長さを推定します。
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
                    await interaction.response.send_message(embed=embed)

                # Reset for a new embed.
                # 新しい埋め込みのためにリセットします。
                embed = discord.Embed(title=self.lang["embed_setting_channel"], color=0x219900)
                message_count = 0
                channel_string = ""
                twitter_user_names_string = ""
                message_flag = True # Set flag to True as subsequent sends will be followups.

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
