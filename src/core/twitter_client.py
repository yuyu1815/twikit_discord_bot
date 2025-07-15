import re
import aiohttp
from twikit import Client
from pathlib import Path

class TwitterClient:
    """
    Twitter API client that encapsulates all Twitter-related functionality.
    This class replaces the functionality in the old twitter_get.py file.

    Twitter APIクライアント。Twitter関連の全ての機能を提供します。
    このクラスは、以前のtwitter_get.pyファイルの機能を置き換えるものです。
    """

    def __init__(self, settings=None, cookie_path=None):
        """
        Initialize the Twitter client.

        Args:
            settings (Settings, optional): Settings object for language support
            cookie_path (str, optional): Path to the cookie file

        Twitterクライアントを初期化します。

        Args:
            settings (Settings, optional): 言語サポートのための設定オブジェクト
            cookie_path (str, optional): クッキーファイルのパス
        """
        self.client = Client('en-US')
        # Determine the path to the cookie file. Defaults to 'data/cookie_edit.json'.
        # クッキーファイルのパスを決定します。デフォルトは 'data/cookie_edit.json' です。
        self.cookie_path = cookie_path or Path(__file__).parent.parent.parent / 'data' / 'cookie_edit.json'
        self.settings = settings

    async def load_client(self):
        """
        Load the Twitter client with cookies.
        This method attempts to load authentication cookies from the specified path,
        which is necessary for making authenticated requests to the Twitter API.

        Raises:
            FileNotFoundError: If the cookie file doesn't exist.

        Twitterクライアントにクッキーをロードします。
        このメソッドは、指定されたパスから認証クッキーをロードしようとします。
        これはTwitter APIへの認証済みリクエストを行うために必要です。

        Raises:
            FileNotFoundError: クッキーファイルが存在しない場合。
        """
        cookie_file = Path(self.cookie_path)
        if not cookie_file.exists():
            # Raise an error if the cookie file is not found, using localized message if settings are available.
            # クッキーファイルが見つからない場合、設定があればローカライズされたメッセージを使用してエラーを発生させます。
            if self.settings:
                raise FileNotFoundError(self.settings.lang_data["twitter_cookie_not_found"].format(self.cookie_path))
            else:
                raise FileNotFoundError(f"Cookie file not found: {self.cookie_path}")

        self.client.load_cookies(str(cookie_file))

    async def twikit_msg(self, user_name):
        """
        Get the latest two tweets from a specified user.
        This method fetches the most recent tweets for a given Twitter user.

        Args:
            user_name (str): The Twitter user's screen name (e.g., "elonmusk").

        Returns:
            tuple: A tuple containing the IDs of the latest tweet and the second latest tweet (latest_tweet_id, next_tweet_id).
                   Returns (None, None) if fetching fails or not enough tweets are found.

        指定されたユーザーの最新の2つのツイートを取得します。
        このメソッドは、指定されたTwitterユーザーの最新のツイートを取得します。

        Args:
            user_name (str): Twitterユーザーのスクリーン名（例: "elonmusk"）。

        Returns:
            tuple: 最新のツイートIDと2番目に新しいツイートIDを含むタプル (latest_tweet_id, next_tweet_id)。
                   取得に失敗した場合や十分なツイートが見つからない場合は (None, None) を返します。
        """
        try:
            user = await self.client.get_user_by_screen_name(user_name)
            # Fetch the two most recent tweets from the user.
            # ユーザーから最新の2つのツイートを取得します。
            tweets = await self.client.get_user_tweets(str(user.id), 'Tweets', count=2)
            return tweets[0].id, tweets[1].id
        except IndexError:
            # Handle cases where fewer than two tweets are found.
            # 2つ未満のツイートしか見つからない場合の処理。
            if self.settings:
                print(self.settings.lang_data["twitter_not_enough_tweets"].format(user_name))
            else:
                print(f"Not enough tweets found for user '{user_name}'")
            return None, None
        except AttributeError as e:
            # Handle cases where the response format is invalid.
            # レスポンス形式が無効な場合の処理。
            if self.settings:
                print(self.settings.lang_data["twitter_invalid_response"].format(user_name, str(e)))
            else:
                print(f"Invalid response format for user '{user_name}': {str(e)}")
            return None, None
        except Exception as e:
            # Catch any other unexpected errors during tweet fetching.
            # ツイート取得中のその他の予期せぬエラーを捕捉します。
            if self.settings:
                print(self.settings.lang_data["twitter_error_getting_tweets"].format(user_name, str(e)))
            else:
                print(f"Error getting tweets for user '{user_name}': {str(e)}")
            return None, None

    async def twikit_id_from_name(self, user_name):
        """
        Get a user's ID from their screen name.
        This method retrieves the full user object, which includes their ID,
        by providing their screen name.

        Args:
            user_name (str): The Twitter user's screen name.

        Returns:
            User: The user object if found.

        Raises:
            UserNotFoundError: If the user with the given screen name does not exist.

        ユーザーのスクリーン名からユーザーIDを取得します。
        このメソッドは、スクリーン名を提供することで、IDを含む完全なユーザーオブジェクトを取得します。

        Args:
            user_name (str): Twitterユーザーのスクリーン名。

        Returns:
            User: 見つかった場合のユーザーオブジェクト。

        Raises:
            UserNotFoundError: 指定されたスクリーン名のユーザーが存在しない場合。
        """
        return await self.client.get_user_by_screen_name(user_name)

    async def get_retweet(self, target_tweet_id):
        """
        Check if a tweet is a retweet or a quote tweet.
        This method determines if a given tweet ID corresponds to a retweet or a quote tweet.

        Args:
            target_tweet_id (str): The ID of the tweet to check.

        Returns:
            bool: True if the tweet is a retweet (not a quote), False otherwise (original tweet, quote tweet, or error).

        ツイートがリツイートまたは引用ツイートであるかを確認します。
        このメソッドは、指定されたツイートIDがリツイートまたは引用ツイートに対応するかどうかを判断します。

        Args:
            target_tweet_id (str): 確認するツイートのID。

        Returns:
            bool: ツイートがリツイートである場合（引用ではない場合）はTrue、それ以外の場合（元のツイート、引用ツイート、またはエラー）はFalse。
        """
        try:
            tweet = await self.client.get_tweet_by_id(str(target_tweet_id))
            # A tweet is considered a retweet if it's not a quote status and its retweeted_tweet ID is different from its own ID.
            # ツイートが引用ステータスではなく、そのretweeted_tweetのIDが自身のIDと異なる場合、リツイートと見なされます。
            if tweet.is_quote_status or (hasattr(tweet, 'retweeted_tweet') and tweet.retweeted_tweet.id == target_tweet_id):
                return False
            else:
                return True
        except AttributeError:
            # This might happen if the tweet object doesn't have expected attributes (e.g., retweeted_tweet).
            # This typically means it's not a retweet in the classic sense.
            # ツイートオブジェクトに期待される属性（例: retweeted_tweet）がない場合に発生する可能性があります。
            # これは通常、それが従来のリツイートではないことを意味します。
            return False
        except Exception as e:
            # Catch any other unexpected errors during the check.
            # チェック中のその他の予期せぬエラーを捕捉します。
            if self.settings:
                print(self.settings.lang_data["twitter_error_checking_retweet"].format(target_tweet_id, str(e)))
            else:
                print(f"Error checking if tweet {target_tweet_id} is a retweet: {str(e)}")
            return False

    async def twitter_msg_get_url(self, msg_url, tweet_id_flag=False, depth=0):
        """
        Extracts and expands URLs from a given tweet URL or ID.
        This method handles both direct tweet URLs and tweet IDs, recursively fetching URLs from quote tweets.

        Args:
            msg_url (str): The tweet URL (e.g., "https://twitter.com/user/status/123") or tweet ID.
            tweet_id_flag (bool, optional): If True, `msg_url` is treated directly as a tweet ID. Defaults to False.
            depth (int, optional): Current recursion depth to prevent infinite loops in quote tweet chains. Defaults to 0.

        Returns:
            list: A list of expanded and filtered URLs found in the tweet and its quoted tweets.
                  Returns None if the tweet ID cannot be extracted or an error occurs.

        指定されたツイートのURLまたはIDからURLを抽出し、展開します。
        このメソッドは、直接のツイートURLとツイートIDの両方を処理し、引用ツイートから再帰的にURLを取得します。

        Args:
            msg_url (str): ツイートのURL（例: "https://twitter.com/user/status/123"）またはツイートID。
            tweet_id_flag (bool, optional): Trueの場合、`msg_url`は直接ツイートIDとして扱われます。デフォルトはFalse。
            depth (int, optional): 引用ツイートチェーンでの無限ループを防ぐための現在の再帰深度。デフォルトは0。

        Returns:
            list: ツイートおよびその引用ツイート内で見つかった、展開されフィルタリングされたURLのリスト。
                  ツイートIDを抽出できない場合やエラーが発生した場合はNoneを返します。
        """
        # Limit recursion depth to prevent performance issues and infinite loops.
        # パフォーマンスの問題と無限ループを防ぐために再帰深度を制限します。
        if depth > 3:
            if self.settings:
                print(self.settings.lang_data["twitter_max_recursion"].format(msg_url))
            else:
                print(f"Reached maximum recursion depth for tweet URL: {msg_url}")
            return None

        tweet_id = None
        if tweet_id_flag:
            tweet_id = msg_url
        elif "https://twitter.com" in msg_url:
            # Extract tweet ID from standard Twitter URL.
            # 標準のTwitter URLからツイートIDを抽出します。
            try:
                tweet_id = re.search(r'twitter\.com/.+/status/(\d+)', msg_url).group(1)
            except (AttributeError, IndexError):
                if self.settings:
                    print(self.settings.lang_data["twitter_invalid_twitter_url"].format(msg_url))
                else:
                    print(f"Invalid Twitter URL format: {msg_url}")
                return None
        elif "https://x.com" in msg_url:
            # Extract tweet ID from X.com URL.
            # X.comのURLからツイートIDを抽出します。
            try:
                tweet_id = re.search(r'x\.com/.+/status/(\d+)', msg_url).group(1)
            except (AttributeError, IndexError):
                if self.settings:
                    print(self.settings.lang_data["twitter_invalid_x_url"].format(msg_url))
                else:
                    print(f"Invalid X URL format: {msg_url}")
                return None

        if tweet_id is None:
            # If no tweet ID could be extracted, return None.
            # ツイートIDを抽出できなかった場合、Noneを返します。
            return None

        try:
            tweet = await self.client.get_tweet_by_id(str(tweet_id))

            tweet_msg = tweet.full_text
            # Regex pattern to find URLs in the tweet text.
            # ツイートテキスト内のURLを見つけるための正規表現パターン。
            url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            urls = re.findall(url_pattern, tweet_msg)

            expanded_urls = []
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    try:
                        # Expand shortened URLs by following redirects.
                        # リダイレクトをたどって短縮URLを展開します。
                        async with session.get(url, allow_redirects=True) as response:
                            expanded_urls.append(str(response.url))
                    except Exception as e:
                        # If URL expansion fails, use the original URL and log the error.
                        # URLの展開に失敗した場合、元のURLを使用し、エラーをログに記録します。
                        if self.settings:
                            print(self.settings.lang_data["twitter_error_expanding_url"].format(url, str(e)))
                        else:
                            print(f"Error expanding URL {url}: {str(e)}")
                        expanded_urls.append(url)  # Use the original URL if expansion fails

            # Filter out Twitter/X.com URLs as they are handled separately or not needed.
            # Twitter/X.comのURLは別途処理されるか、不要なためフィルタリングします。
            filtered_urls = [url for url in expanded_urls if "https://twitter.com" not in url and "https://x.com" not in url]

            has_quote = False
            try:
                # Check if the tweet is a quote tweet.
                # ツイートが引用ツイートであるかを確認します。
                _ = tweet.quote.id
                has_quote = True
            except AttributeError:
                # Not a quote tweet.
                # 引用ツイートではない。
                pass

            if has_quote:
                # Recursively get URLs from the quoted tweet.
                # 引用ツイートから再帰的にURLを取得します。
                retweet_urls = await self.twitter_msg_get_url(tweet.quote.id, True, depth + 1)
                # Add the fxtwitter.com URL for the quoted tweet.
                # 引用ツイートのfxtwitter.comのURLを追加します。
                filtered_urls.append(f"https://fxtwitter.com/{tweet.user.screen_name}/status/{tweet.quote.id}")
                if retweet_urls:
                    filtered_urls.extend(retweet_urls)

            return filtered_urls if filtered_urls else None

        except AttributeError as e:
            # Handle cases where tweet data is invalid or missing expected attributes.
            # ツイートデータが無効であるか、期待される属性が欠落している場合の処理。
            if self.settings:
                print(self.settings.lang_data["twitter_invalid_tweet_data"].format(tweet_id, str(e)))
            else:
                print(f"Invalid tweet data for tweet {tweet_id}: {str(e)}")
            return None
        except Exception as e:
            # Catch any other unexpected errors during URL extraction.
            # URL抽出中のその他の予期せぬエラーを捕捉します。
            if self.settings:
                print(self.settings.lang_data["twitter_error_getting_urls"].format(tweet_id, str(e)))
            else:
                print(f"Error getting URLs from tweet {tweet_id}: {str(e)}")
            return None

    async def user_exist(self, user_name):
        """
        Check if a Twitter user exists by their screen name.

        Args:
            user_name (str): The Twitter user's screen name.

        Returns:
            bool: True if the user exists, False otherwise.

        Twitterユーザーがスクリーン名で存在するかどうかを確認します。

        Args:
            user_name (str): Twitterユーザーのスクリーン名。

        Returns:
            bool: ユーザーが存在する場合はTrue、それ以外の場合はFalse。
        """
        try:
            await self.client.get_user_by_screen_name(user_name)
            return True
        except Exception as e:
            # This exception is expected if the user does not exist.
            # ユーザーが存在しない場合、この例外は予期されます。
            if self.settings:
                print(self.settings.lang_data["twitter_user_not_exist"].format(user_name, str(e)))
            else:
                print(f"User '{user_name}' does not exist: {str(e)}")
            return False
