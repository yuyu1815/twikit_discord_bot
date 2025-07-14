import discord
import re
from discord.ext import commands

class URLFixerCog(commands.Cog):
    """
    Cog for fixing URLs in messages.
    This includes replacing Twitter/X URLs with fxtwitter URLs for better embeds.
    """

    def __init__(self, bot):
        """
        Initialize the cog with a reference to the bot.

        Args:
            bot: The bot instance
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Event listener for messages.
        Replaces Twitter/X URLs with fxtwitter URLs and TikTok URLs with fxtiktok URLs.

        Args:
            message: The message object
        """
        # Ignore messages from bots
        if message.author.bot:
            return

        print(f"{message.author.name}: {message.content}")

        # Get guild settings from database
        guild_settings = self.bot.db.get_guild_settings(message.guild.id)

        # If no settings exist, create default settings
        if guild_settings is None:
            self.bot.db.update_guild_settings(
                message.guild.id,
                twitter_updates_enabled=True,
                url_preview_enabled=True,
                cool_down_minutes=1
            )
            guild_settings = self.bot.db.get_guild_settings(message.guild.id)

        # Skip if URL preview is disabled in database
        if not guild_settings['url_preview_enabled']:
            return

        # Define URL patterns to replace using a dictionary for better readability
        url_replacements = {
            'https://x.com': 'https://fxtwitter.com',
            'https://twitter.com': 'https://fxtwitter.com',
            'https://www.tiktok.com': 'https://fxtiktok.com',
            'https://tiktok.com': 'https://fxtiktok.com'
        }

        # Find URLs in the message
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = re.findall(url_pattern, message.content)

        if not urls:
            return

        # Process all URLs in the message
        replaced_urls = []
        additional_urls = []

        for url in urls:
            # Check if the URL matches any of the patterns
            for original_url, replacement_url in url_replacements.items():
                if original_url in url:
                    replaced_url = url.replace(original_url, replacement_url)
                    replaced_urls.append(replaced_url)

                    # If the URL was replaced with fxtwitter, check for additional URLs in the tweet
                    if 'https://fxtwitter.com' in replaced_url:
                        print(url)
                        other_url = await self.bot.twitter_client.twitter_msg_get_url(url)
                        if other_url is not None:
                            # Collect additional URLs from the tweet
                            for tweet_url in other_url:
                                if "https://fxtwitter.com" in tweet_url:
                                    additional_urls.append(f"[￶]({tweet_url})")
                                else:
                                    additional_urls.append(tweet_url)

                    break

        # Only edit the message once if any URLs were replaced
        if replaced_urls:
            await message.edit(suppress=True)

            # Batch messages to reduce API calls
            await self._send_batched_messages(message.channel, replaced_urls, additional_urls)

    async def _send_batched_messages(self, channel, replaced_urls, additional_urls):
        """
        Send URLs in batches to reduce the number of API calls.

        Args:
            channel: The channel to send messages to
            replaced_urls: List of replaced URLs to send
            additional_urls: List of additional URLs found in tweets
        """
        # Format replaced URLs
        formatted_replaced_urls = [f"[￶]({url})" for url in replaced_urls]

        # Combine all URLs
        all_urls = formatted_replaced_urls + additional_urls

        # Discord message limit is 2000 characters
        MAX_MESSAGE_LENGTH = 2000

        # Batch URLs into messages
        current_message = ""

        for url in all_urls:
            # If adding this URL would exceed the limit, send the current message and start a new one
            if len(current_message) + len(url) + 1 > MAX_MESSAGE_LENGTH:
                if current_message:
                    await channel.send(current_message)
                current_message = url
            else:
                # Add URL to current message with a newline if not empty
                if current_message:
                    current_message += "\n" + url
                else:
                    current_message = url

        # Send any remaining message
        if current_message:
            await channel.send(current_message)
