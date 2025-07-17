import discord
import re
import asyncio
from discord.ext import commands
from ..core.twitter_analyzer import analyze_tweet_with_manager

class URLFixerCog(commands.Cog):
    """
    Cog for fixing URLs in messages.
    This includes replacing Twitter/X URLs with fxtwitter URLs and TikTok URLs with fxtiktok URLs for better embeds.
    It also analyzes Twitter/X URLs to determine if they are retweets or replies, and expands them accordingly.

    メッセージ内のURLを修正するためのコグです。
    これには、より良い埋め込みのためにTwitter/XのURLをfxtwitterのURLに、TikTokのURLをfxtiktokのURLに置き換える機能が含まれます。
    また、Twitter/XのURLがリツイートか返信かを判断し、それに応じて展開する機能も含まれます。
    """

    def __init__(self, bot):
        """
        Initialize the cog with a reference to the bot.
        The bot instance provides access to settings and other necessary components.

        Args:
            bot: The bot instance (MyBot).

        ボットへの参照でコグを初期化します。
        ボットインスタンスは、設定やその他の必要なコンポーネントへのアクセスを提供します。

        Args:
            bot: ボットインスタンス (MyBot)。
        """
        self.bot = bot

    def extract_tweet_id(self, url):
        """
        Extract the tweet ID from a Twitter/X URL.

        Args:
            url (str): The Twitter/X URL.

        Returns:
            str: The tweet ID if found, None otherwise.

        Twitter/XのURLからツイートIDを抽出します。

        Args:
            url (str): Twitter/XのURL。

        Returns:
            str: 見つかった場合はツイートID、それ以外の場合はNone。
        """
        # Pattern for Twitter/X URLs with status
        pattern = r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Event listener for messages.
        This method is triggered whenever a message is sent in a Discord channel.
        It processes messages to replace specific URLs for better embedding.

        Args:
            message: The message object from Discord.

        メッセージのイベントリスナーです。
        このメソッドは、Discordチャンネルでメッセージが送信されるたびにトリガーされます。
        特定のURLをより良い埋め込みのために置き換えるためにメッセージを処理します。

        Args:
            message: Discordからのメッセージオブジェクト。
        """
        # Ignore messages from bots to prevent infinite loops or unnecessary processing.
        # 無限ループや不要な処理を防ぐため、ボットからのメッセージは無視します。
        if message.author.bot:
            return

        if self.bot.settings:
            print(self.bot.settings.lang_data.get("url_fixer_message_log", "{0}: {1}").format(message.author.name, message.content))
        else:
            print(f"{message.author.name}: {message.content}")

        # Retrieve guild settings from the database.
        # データベースからギルド設定を取得します。
        guild_settings = self.bot.db.get_guild_settings(message.guild.id)

        # If no settings exist for the guild, create default settings.
        # ギルドの設定が存在しない場合、デフォルト設定を作成します。
        if guild_settings is None:
            self.bot.db.update_guild_settings(
                message.guild.id,
                twitter_updates_enabled=True,
                url_preview_enabled=True,
                cool_down_minutes=1
            )
            guild_settings = self.bot.db.get_guild_settings(message.guild.id)

        # Skip processing if URL preview is disabled in the guild settings.
        # ギルド設定でURLプレビューが無効になっている場合は処理をスキップします。
        if not guild_settings['url_preview_enabled']:
            return

        # Define URL patterns and their replacements using a dictionary for clarity and easy modification.
        # 明確さと変更の容易さのために、辞書を使用してURLパターンとその置換を定義します。
        url_replacements = {
            'https://x.com': 'https://fxtwitter.com',
            'https://twitter.com': 'https://fxtwitter.com',
            'https://www.tiktok.com': 'https://fxtiktok.com',
            'https://tiktok.com': 'https://fxtiktok.com'
        }

        # Find all URLs in the message content.
        # メッセージコンテンツ内のすべてのURLを見つけます。
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = re.findall(url_pattern, message.content)

        if not urls:
            # If no URLs are found, there's nothing to do.
            # URLが見つからない場合、何もしません。
            return

        replaced_urls = []
        additional_urls = []

        for url in urls:
            # Iterate through defined replacements to find a match.
            # 定義された置換を反復処理して一致するものを見つけます。
            for original_url, replacement_url in url_replacements.items():
                if original_url in url:
                    replaced_url = url.replace(original_url, replacement_url)
                    replaced_urls.append(replaced_url)

                    # Log the URL if settings are available
                    # 設定が利用可能な場合はURLをログに記録します
                    if 'https://fxtwitter.com' in replaced_url:
                        if self.bot.settings:
                            print(self.bot.settings.lang_data.get("url_fixer_url_log", "URL: {0}").format(url))
                        else:
                            print(url)

                        # Extract tweet ID and analyze the tweet
                        # ツイートIDを抽出し、ツイートを分析します
                        tweet_id = self.extract_tweet_id(url)
                        if tweet_id:
                            try:
                                # Analyze the tweet to determine if it's a retweet or reply
                                # ツイートがリツイートか返信かを判断するために分析します
                                analysis_result = await analyze_tweet_with_manager(self.bot.twitter_client_manager, tweet_id)

                                # Handle retweets - add the original tweet URL
                                # リツイートの処理 - 元のツイートのURLを追加します
                                if analysis_result.get('type') == 'retweet' and 'original_tweet' in analysis_result:
                                    original_id = analysis_result['original_tweet']['id']
                                    original_user = analysis_result['original_tweet']['user_screen_name']
                                    original_url = f"https://fxtwitter.com/{original_user}/status/{original_id}"
                                    additional_urls.append(original_url)

                                    if self.bot.settings:
                                        print(self.bot.settings.lang_data.get("url_fixer_retweet_expanded", "Expanded retweet: {0}").format(original_url))
                                    else:
                                        print(f"Expanded retweet: {original_url}")

                                # Handle replies - add the thread URLs
                                # 返信の処理 - スレッドのURLを追加します
                                elif analysis_result.get('type') == 'reply' and 'reply_thread' in analysis_result:
                                    thread = analysis_result['reply_thread']
                                    for tweet in thread:
                                        if tweet['id'] != tweet_id:  # Skip the original tweet that was already processed
                                            thread_url = f"https://fxtwitter.com/{tweet['user_screen_name']}/status/{tweet['id']}"
                                            additional_urls.append(thread_url)

                                            if self.bot.settings:
                                                print(self.bot.settings.lang_data.get("url_fixer_reply_expanded", "Expanded reply: {0}").format(thread_url))
                                            else:
                                                print(f"Expanded reply: {thread_url}")
                            except Exception as e:
                                # Log any errors during tweet analysis
                                # ツイート分析中のエラーをログに記録します
                                if self.bot.settings:
                                    print(self.bot.settings.lang_data.get("url_fixer_analysis_error", "Error analyzing tweet: {0}").format(str(e)))
                                else:
                                    print(f"Error analyzing tweet: {str(e)}")

                    break # Only apply one replacement per URL.

        # Only edit the message once if any URLs were replaced to avoid multiple edits.
        # 複数の編集を避けるため、URLが置き換えられた場合にのみメッセージを一度だけ編集します。
        if replaced_urls:
            await message.edit(suppress=True) # Suppress embeds from original URLs.

            # Send the processed URLs in batches to adhere to Discord message limits.
            # Discordのメッセージ制限に準拠するために、処理されたURLをバッチで送信します。
            await self._send_batched_messages(message.channel, replaced_urls, additional_urls)

    async def _send_batched_messages(self, channel, replaced_urls, additional_urls):
        """
        Send URLs in batches to reduce the number of API calls and adhere to Discord's message length limit.

        Args:
            channel: The Discord channel to send messages to.
            replaced_urls: A list of URLs that were replaced (e.g., original Twitter/X URLs converted to fxtwitter).
            additional_urls: A list of URLs found within the content of the processed tweets.

        API呼び出しの数を減らし、Discordのメッセージ長制限に準拠するために、URLをバッチで送信します。

        Args:
            channel: メッセージを送信するDiscordチャンネル。
            replaced_urls: 置換されたURLのリスト（例: 元のTwitter/XのURLがfxtwitterに変換されたもの）。
            additional_urls: 処理されたツイートのコンテンツ内で見つかったURLのリスト。
        """
        # Format all URLs with a zero-width space to hide the link text in Discord.
        # Discordでリンクテキストを非表示にするために、すべてのURLをゼロ幅スペースでフォーマットします。
        formatted_replaced_urls = [f"[￶]({url})" for url in replaced_urls]
        formatted_additional_urls = [f"[￶]({url})" for url in additional_urls]

        # Combine all formatted URLs to be sent, with replaced URLs at the end.
        # フォーマットされたすべてのURLを送信するために結合します。置換されたURLは最後に配置します。
        all_urls = formatted_additional_urls + formatted_replaced_urls

        # Discord's maximum message length.
        # Discordの最大メッセージ長。
        MAX_MESSAGE_LENGTH = 2000

        current_message = ""

        for url in all_urls:
            # Check if adding the current URL would exceed the message length limit.
            # 現在のURLを追加するとメッセージ長制限を超えるかどうかを確認します。
            if len(current_message) + len(url) + 1 > MAX_MESSAGE_LENGTH:
                if current_message:
                    # Send the current message if it's not empty.
                    # 現在のメッセージが空でない場合、送信します。
                    await channel.send(current_message)
                current_message = url # Start a new message with the current URL.
            else:
                # Add URL to current message with a newline if the message is not empty.
                # メッセージが空でない場合、改行を追加して現在のメッセージにURLを追加します。
                if current_message:
                    current_message += " " + url
                else:
                    current_message = url # If empty, just set the URL as the message.

        # Send any remaining message after the loop finishes.
        # ループ終了後に残っているメッセージを送信します。
        if current_message:
            await channel.send(current_message)
