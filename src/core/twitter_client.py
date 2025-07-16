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
            # A tweet is considered a retweet if it's not a quote status and its retweeted_tweet ID is different from its own ID.
            # If it's a quote tweet (is_quote_status is True) or if the retweeted_tweet ID is the same as the target_tweet_id (meaning it's the original tweet being checked), it's not a "pure" retweet.
            # ツイートが引用ステータスではなく、そのretweeted_tweetのIDが自身のIDと異なる場合、リツイートと見なされます。
            # 引用ツイートである場合（is_quote_statusがTrue）、またはretweeted_tweetのIDがtarget_tweet_idと同じ場合（チェックされているのが元のツイートであることを意味する）、それは「純粋な」リツイートではありません。
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
