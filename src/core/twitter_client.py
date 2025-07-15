import re
import aiohttp
from twikit import Client
from pathlib import Path

class TwitterClient:
    """
    Twitter API client that encapsulates all Twitter-related functionality.
    This class replaces the functionality in the old twitter_get.py file.
    """

    def __init__(self, settings=None, cookie_path=None):
        """
        Initialize the Twitter client.

        Args:
            settings (Settings, optional): Settings object for language support
            cookie_path (str, optional): Path to the cookie file
        """
        self.client = Client('en-US')
        self.cookie_path = cookie_path or Path(__file__).parent.parent.parent / 'data' / 'cookie_edit.json'
        self.settings = settings

    async def load_client(self):
        """
        Load the Twitter client with cookies.

        Raises:
            FileNotFoundError: If the cookie file doesn't exist
        """
        cookie_file = Path(self.cookie_path)
        if not cookie_file.exists():
            if self.settings:
                raise FileNotFoundError(self.settings.lang_data["twitter_cookie_not_found"].format(self.cookie_path))
            else:
                raise FileNotFoundError(f"Cookie file not found: {self.cookie_path}")

        self.client.load_cookies(str(cookie_file))

    async def twikit_msg(self, user_name):
        """
        Get the latest tweets from a user.

        Args:
            user_name (str): The Twitter user name

        Returns:
            tuple: (latest_tweet_id, next_tweet_id) or (None, None) if failed
        """
        try:
            user = await self.client.get_user_by_screen_name(user_name)
            tweets = await self.client.get_user_tweets(str(user.id), 'Tweets', count=2)
            return tweets[0].id, tweets[1].id
        except IndexError:
            if self.settings:
                print(self.settings.lang_data["twitter_not_enough_tweets"].format(user_name))
            else:
                print(f"Not enough tweets found for user '{user_name}'")
            return None, None
        except AttributeError as e:
            if self.settings:
                print(self.settings.lang_data["twitter_invalid_response"].format(user_name, str(e)))
            else:
                print(f"Invalid response format for user '{user_name}': {str(e)}")
            return None, None
        except Exception as e:
            if self.settings:
                print(self.settings.lang_data["twitter_error_getting_tweets"].format(user_name, str(e)))
            else:
                print(f"Error getting tweets for user '{user_name}': {str(e)}")
            return None, None

    async def twikit_id_from_name(self, user_name):
        """
        Get a user's ID from their screen name.

        Args:
            user_name (str): The Twitter user name

        Returns:
            User: The user object

        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        return await self.client.get_user_by_screen_name(user_name)

    async def get_retweet(self, target_tweet_id):
        """
        Check if a tweet is a retweet.

        Args:
            target_tweet_id (str): The tweet ID

        Returns:
            bool: True if the tweet is a retweet, False otherwise
        """
        try:
            tweet = await self.client.get_tweet_by_id(str(target_tweet_id))
            if tweet.is_quote_status or tweet.retweeted_tweet.id == target_tweet_id:
                return False
            else:
                return True
        except AttributeError:
            # This might happen if the tweet doesn't have a retweeted_tweet attribute
            return False
        except Exception as e:
            if self.settings:
                print(self.settings.lang_data["twitter_error_checking_retweet"].format(target_tweet_id, str(e)))
            else:
                print(f"Error checking if tweet {target_tweet_id} is a retweet: {str(e)}")
            return False

    async def twitter_msg_get_url(self, msg_url, tweet_id_flag=False, depth=0):
        """
        Get URLs from a tweet.

        Args:
            msg_url (str): The tweet URL or ID
            tweet_id_flag (bool): Whether msg_url is a tweet ID
            depth (int): Current recursion depth

        Returns:
            list: List of URLs or None if failed
        """
        # Limit recursion depth to prevent performance issues
        if depth > 3:
            if self.settings:
                print(self.settings.lang_data["twitter_max_recursion"].format(msg_url))
            else:
                print(f"Reached maximum recursion depth for tweet URL: {msg_url}")
            return None

        # Extract tweet ID from URL
        tweet_id = None
        if tweet_id_flag:
            tweet_id = msg_url
        elif "https://twitter.com" in msg_url:
            try:
                tweet_id = re.search(r'twitter\.com/.+/status/(\d+)', msg_url).group(1)
            except (AttributeError, IndexError):
                if self.settings:
                    print(self.settings.lang_data["twitter_invalid_twitter_url"].format(msg_url))
                else:
                    print(f"Invalid Twitter URL format: {msg_url}")
                return None
        elif "https://x.com" in msg_url:
            try:
                tweet_id = re.search(r'x\.com/.+/status/(\d+)', msg_url).group(1)
            except (AttributeError, IndexError):
                if self.settings:
                    print(self.settings.lang_data["twitter_invalid_x_url"].format(msg_url))
                else:
                    print(f"Invalid X URL format: {msg_url}")
                return None

        if tweet_id is None:
            return None

        try:
            tweet = await self.client.get_tweet_by_id(str(tweet_id))

            tweet_msg = tweet.full_text
            # Extract URLs from tweet text
            url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            urls = re.findall(url_pattern, tweet_msg)

            # Expand shortened URLs
            expanded_urls = []
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    try:
                        async with session.get(url, allow_redirects=True) as response:
                            expanded_urls.append(str(response.url))
                    except Exception as e:
                        if self.settings:
                            print(self.settings.lang_data["twitter_error_expanding_url"].format(url, str(e)))
                        else:
                            print(f"Error expanding URL {url}: {str(e)}")
                        expanded_urls.append(url)  # Use the original URL if expansion fails

            # Filter out Twitter URLs
            filtered_urls = [url for url in expanded_urls if "https://twitter.com" not in url and "https://x.com" not in url]

            # Check if this is a quote tweet
            has_quote = False
            try:
                _ = tweet.quote.id
                has_quote = True
            except AttributeError:
                pass

            if has_quote:
                # Get URLs from the quoted tweet (with increased depth)
                retweet_urls = await self.twitter_msg_get_url(tweet.quote.id, True, depth + 1)
                # Add the quoted tweet URL
                filtered_urls.append(f"https://fxtwitter.com/{tweet.user.screen_name}/status/{tweet.quote.id}")
                if retweet_urls:
                    filtered_urls.extend(retweet_urls)

            return filtered_urls if filtered_urls else None

        except AttributeError as e:
            if self.settings:
                print(self.settings.lang_data["twitter_invalid_tweet_data"].format(tweet_id, str(e)))
            else:
                print(f"Invalid tweet data for tweet {tweet_id}: {str(e)}")
            return None
        except Exception as e:
            if self.settings:
                print(self.settings.lang_data["twitter_error_getting_urls"].format(tweet_id, str(e)))
            else:
                print(f"Error getting URLs from tweet {tweet_id}: {str(e)}")
            return None

    async def user_exist(self, user_name):
        """
        Check if a user exists.

        Args:
            user_name (str): The Twitter user name

        Returns:
            bool: True if the user exists, False otherwise
        """
        try:
            await self.client.get_user_by_screen_name(user_name)
            return True
        except Exception as e:
            # This is an expected error when the user doesn't exist
            if self.settings:
                print(self.settings.lang_data["twitter_user_not_exist"].format(user_name, str(e)))
            else:
                print(f"User '{user_name}' does not exist: {str(e)}")
            return False
