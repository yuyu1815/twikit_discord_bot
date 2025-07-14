import discord
from discord import app_commands
from discord.ext import commands

class TwitterCommandsCog(commands.Cog):
    """
    Cog for Twitter-related commands.
    This includes commands for setting up Twitter feeds, checking settings, etc.
    """

    def __init__(self, bot):
        """
        Initialize the cog with a reference to the bot.

        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.lang = bot.settings.lang_data

    async def message_send(self, interaction, msg, ephemeral=False):
        """
        Send a message to both Discord and the console.

        Args:
            interaction: The interaction object
            msg: The message to send
            ephemeral: Whether the message should be ephemeral
        """
        print(msg)
        await interaction.response.send_message(msg, ephemeral=ephemeral)

    @app_commands.command(name='set_twitter')
    async def set_command(self, interaction: discord.Interaction, twitter_user_name: str):
        """
        Set up a Twitter feed for a channel.

        Args:
            interaction: The interaction object
            twitter_user_name: The Twitter username to follow
        """
        # Get channel and guild IDs
        channel_id = interaction.channel_id
        guild_id = interaction.guild_id

        # Get guild settings from database
        guild_settings = self.bot.db.get_guild_settings(guild_id)

        # If no settings exist yet, create default settings
        if guild_settings is None:
            self.bot.db.update_guild_settings(
                guild_id,
                twitter_updates_enabled=True,
                url_preview_enabled=True,
                cool_down_minutes=1
            )
            guild_settings = self.bot.db.get_guild_settings(guild_id)

        # Check if Twitter updates are enabled
        if not guild_settings['twitter_updates_enabled']:
            await self.message_send(interaction, self.lang["setting_flag_msg"], True)
            return

        # Check if the Twitter user exists
        if not await self.bot.twitter_client.user_exist(twitter_user_name):
            await self.message_send(interaction, self.lang["unknown_user_msg"], True)
            return

        # Try to add the feed to the database
        success = self.bot.db.add_twitter_feed(guild_id, channel_id, twitter_user_name)

        # If the feed already exists, show error message
        if not success:
            await self.message_send(interaction, self.lang["duplicated_user_msg"], True)
            return

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='del_twitter')
    async def del_command(self, interaction: discord.Interaction, user_name: str):
        """
        Remove a Twitter feed from a channel.

        Args:
            interaction: The interaction object
            user_name: The Twitter username to unfollow
        """
        # Get channel and guild IDs
        channel_id = interaction.channel_id
        guild_id = interaction.guild_id

        # Try to remove the feed from the database
        success = self.bot.db.remove_twitter_feed(channel_id, user_name)

        if success:
            await self.message_send(interaction, self.lang["setting_completed_msg"], True)
        else:
            # Not found in database
            await self.message_send(interaction, self.lang["no_user_registration_msg"], True)

    @app_commands.command(name='check-time')
    async def cool_down(self, interaction: discord.Interaction, minutes: int):
        """
        Set the cool down time for Twitter updates.

        Args:
            interaction: The interaction object
            minutes: The cool down time in minutes
        """
        # Ensure minutes is at least 1
        minutes = max(1, minutes)

        # Update database settings
        self.bot.db.update_guild_settings(interaction.guild_id, cool_down_minutes=minutes)

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='change-setting-twitter-get')
    async def change_setting_twitter_get(self, interaction: discord.Interaction, mode: bool):
        """
        Enable or disable Twitter updates.

        Args:
            interaction: The interaction object
            mode: Whether to enable Twitter updates
        """
        # Get guild ID
        guild_id = interaction.guild_id

        # Update database settings
        self.bot.db.update_guild_settings(guild_id, twitter_updates_enabled=mode)

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='change-setting-url-preview')
    async def change_setting_url_preview(self, interaction: discord.Interaction, mode: bool):
        """
        Enable or disable URL previews.

        Args:
            interaction: The interaction object
            mode: Whether to enable URL previews
        """
        # Get guild ID
        guild_id = interaction.guild_id

        # Update database settings
        self.bot.db.update_guild_settings(guild_id, url_preview_enabled=mode)

        await self.message_send(interaction, self.lang["setting_completed_msg"], True)

    @app_commands.command(name='check-settings')
    async def check_setting(self, interaction: discord.Interaction):
        """
        Check the current settings.

        Args:
            interaction: The interaction object
        """
        # Get guild ID
        guild_id = interaction.guild_id

        # Get settings from database
        guild_settings = self.bot.db.get_guild_settings(guild_id)

        # If no settings exist, create default settings
        if guild_settings is None:
            self.bot.db.update_guild_settings(
                guild_id,
                twitter_updates_enabled=True,
                url_preview_enabled=True,
                cool_down_minutes=1
            )
            guild_settings = self.bot.db.get_guild_settings(guild_id)

        # Get Twitter feeds from database
        feeds = self.bot.db.get_twitter_feeds(guild_id)

        # Extract feeds from database
        setting_channels = [feed['channel_id'] for feed in feeds]
        twitter_user_names = [feed['twitter_user_name'] for feed in feeds]

        # Extract settings from database
        cool_down_time = guild_settings['cool_down_minutes']
        twitter_updates_enabled = guild_settings['twitter_updates_enabled']
        url_preview_enabled = guild_settings['url_preview_enabled']

        # Create embed
        embed = discord.Embed(
            title=self.lang["embed_setting"],
            description=f"{self.lang['embed_check_time']} : {cool_down_time}{self.lang['embed_minutes']}\n"
                       f"{self.lang['embed_new_tweet']} : {twitter_updates_enabled}\n"
                       f"{self.lang['embed_change_fxtwitter']}：{url_preview_enabled}",
            color=0x219900
        )

        # Initialize strings for channels and Twitter users
        channel_string = ""
        twitter_user_names_string = ""
        message_count = 0
        message_flag = False

        # Add channels and Twitter users to the embed
        for setting_channel, twitter_user_name in zip(setting_channels, twitter_user_names):
            message_count += 4 + len(str(setting_channel)) + 18 + len(twitter_user_name)

            # If we're approaching Discord's limit, send the current embed and create a new one
            if message_count >= 1024:
                embed.add_field(name=self.lang["embed_setting_channel"], value=channel_string or "None", inline=True)
                embed.add_field(name=self.lang["embed_setting_user"], value=twitter_user_names_string or "None", inline=True)

                if message_flag:
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.response.send_message(embed=embed)

                # Create a new embed
                embed = discord.Embed(title=self.lang["embed_setting_channel"], color=0x219900)
                message_count = 0
                channel_string = ""
                twitter_user_names_string = ""
                message_flag = True

            # Add the channel and Twitter user to the strings
            channel_string += f"<#{setting_channel}>\n"
            twitter_user_names_string += f"[{twitter_user_name}](https://x.com/{twitter_user_name})\n"

        # Add the remaining channels and Twitter users to the embed
        embed.add_field(name=self.lang["embed_setting_channel"], value=channel_string or "None", inline=True)
        embed.add_field(name=self.lang["embed_setting_user"], value=twitter_user_names_string or "None", inline=True)

        # Send the embed
        if message_flag:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)
