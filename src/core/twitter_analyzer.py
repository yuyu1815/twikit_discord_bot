"""
This module provides functions for analyzing Twitter tweets, including
determining tweet types (retweet, reply, normal), extracting tweet threads,
and fetching RSS-like tweet feeds. It leverages the twikit library and
integrates with the TwitterClientManager for robust client handling.

このモジュールは、Twitterのツイートを分析するための機能を提供します。
これには、ツイートのタイプ（リツイート、返信、通常）の判別、ツイートスレッドの抽出、
RSSのようなツイートフィードの取得が含まれます。twikitライブラリを活用し、
堅牢なクライアント処理のためにTwitterClientManagerと統合されています。
"""

import asyncio
from typing import Dict, List, Any, Optional, Union

from twikit.tweet import Tweet
from twikit import Client
from twikit.guest import GuestClient

from .twitter_client_manager import TwitterClientManager

async def get_tweet_thread(client: Union[GuestClient, Client], tweet_id: str, settings=None) -> List[Tweet]:
    """
    Recursively retrieves the full thread of tweets that a reply tweet belongs to.
    The thread is ordered from the oldest tweet to the newest.

    返信ツイートが属するツイートの完全なスレッドを再帰的に取得します。
    スレッドは最も古いツイートから最も新しいツイートへと順序付けられています。

    Args:
        client: A twikit client instance (either GuestClient or Client) used to fetch tweet data.
                ツイートデータを取得するために使用されるtwikitクライアントインスタンス（GuestClientまたはClient）。
        tweet_id: The ID of the reply tweet for which to retrieve the thread.
                  スレッドを取得する返信ツイートのID。

    Returns:
        List[Tweet]: A list of Tweet objects representing the thread, ordered from oldest to newest.
                     スレッドを表すTweetオブジェクトのリスト。最も古いものから最も新しいものへ順序付けられています。
    """
    thread = []
    current_tweet_id = tweet_id

    # Loop to traverse up the reply chain until the original tweet is found or an error occurs.
    # 元のツイートが見つかるかエラーが発生するまで、返信チェーンを遡るループ。
    while current_tweet_id:
        try:
            tweet = await client.get_tweet_by_id(str(current_tweet_id))
            if tweet is None:
                # If a tweet is not found, stop traversing the thread.
                # ツイートが見つからない場合、スレッドの走査を停止します。
                break

            # Insert the current tweet at the beginning of the list to maintain oldest-to-newest order.
            # 最も古いものから最も新しいものへの順序を維持するために、現在のツイートをリストの先頭に挿入します。
            thread.insert(0, tweet)
            # Move to the parent tweet in the reply chain.
            # 返信チェーンの親ツイートに移動します。
            current_tweet_id = tweet.in_reply_to
        except Exception as e:
            # If an error occurs during tweet fetching (e.g., tweet deleted, API error),
            # return what has been collected so far.
            # ツイートの取得中にエラーが発生した場合（例: ツイートが削除された、APIエラー）、
            # これまでに収集したものを返します。
            if settings:
                print(settings.lang_data.get("twitter_error_fetching_thread", "Error fetching tweet in thread: {0}").format(e))
            else:
                print(f"Error fetching tweet in thread: {e}")
            break

    return thread

async def analyze_tweet(client: Union[GuestClient, Client], tweet_id: str) -> Dict[str, Any]:
    """
    Analyzes a single tweet to determine its type (normal, retweet, or reply) and extracts
    relevant information based on its type.

    単一のツイートを分析し、そのタイプ（通常、リツイート、返信）を判別し、
    そのタイプに基づいて関連情報を抽出します。

    Args:
        client: A twikit client instance (either GuestClient or Client) used to fetch tweet data.
                ツイートデータを取得するために使用されるtwikitクライアントインスタンス（GuestClientまたはClient）。
        tweet_id: The ID of the tweet to analyze.
                  分析するツイートのID。

    Returns:
        Dict[str, Any]: A dictionary containing the analysis results, including the tweet type
                        and specific data for retweets or replies.
                        分析結果を含む辞書。ツイートタイプと、リツイートまたは返信の特定のデータが含まれます。
    """
    result = {
        "tweet_id": tweet_id,
        "type": "unknown",  # Default type, will be updated based on analysis.
                            # デフォルトのタイプ。分析に基づいて更新されます。
    }

    try:
        # Attempt to fetch the tweet by its ID.
        # ツイートをIDで取得しようとします。
        tweet = await client.get_tweet_by_id(str(tweet_id))

        if tweet is None:
            result["error"] = "Tweet not found"
            return result

        # Store basic information about the tweet.
        # ツイートに関する基本情報を保存します。
        result["tweet_data"] = {
            "id": tweet.id,
            "user_screen_name": tweet.user.screen_name,
            "text": tweet.text
        }

        # Check if the tweet is a retweet.
        # ツイートがリツイートであるかを確認します。
        if hasattr(tweet, 'retweeted_tweet') and tweet.retweeted_tweet:
            result["type"] = "retweet"
            result["original_tweet"] = {
                "id": tweet.retweeted_tweet.id,
                "user_screen_name": tweet.retweeted_tweet.user.screen_name,
                "text": tweet.retweeted_tweet.text
            }
            return result

        # Check if the tweet is a reply to another tweet.
        # ツイートが別のツイートへの返信であるかを確認します。
        if tweet.in_reply_to:
            result["type"] = "reply"
            # If it's a reply, retrieve the entire conversation thread.
            # 返信の場合、会話スレッド全体を取得します。
            thread = await get_tweet_thread(client, tweet_id)

            # Format the thread data for inclusion in the result.
            # 結果に含めるためにスレッドデータをフォーマットします。
            result["reply_thread"] = []
            for t in thread:
                result["reply_thread"].append({
                    "id": t.id,
                    "user_screen_name": t.user.screen_name,
                    "text": t.text
                })
            return result

        # If the tweet is neither a retweet nor a reply, it is considered a normal tweet.
        # ツイートがリツイートでも返信でもない場合、通常のツイートと見なされます。
        result["type"] = "normal"
        return result

    except Exception as e:
        # Catch any exceptions during analysis and report the error.
        # 分析中の例外を捕捉し、エラーを報告します。
        result["error"] = str(e)
        return result

async def get_rss_like_tweets(client: Client, user_id: Optional[str] = None, screen_name: Optional[str] = None, tweet_type: str = 'Tweets', count: int = 10, settings=None) -> List[Tweet]:
    """
    Fetches the latest tweets from a specified user, mimicking an RSS feed.
    This function requires an authenticated client.

    指定されたユーザーの最新のツイートを取得し、RSSフィードのように機能します。
    この関数は認証済みクライアントを必要とします。

    Args:
        client: An authenticated twikit Client instance.
                認証済みのtwikit Clientインスタンス。
        user_id: The ID of the user to get tweets from. Required if `screen_name` is not provided.
                 ツイートを取得するユーザーのID。`screen_name`が提供されない場合は必須。
        screen_name: The screen name of the user to get tweets from. Required if `user_id` is not provided.
                     ツイートを取得するユーザーのスクリーン名。`user_id`が提供されない場合は必須。
        tweet_type: The type of tweets to retrieve (e.g., 'Tweets', 'Replies', 'Media').
                    ツイートの種類（例: 'Tweets'、'Replies'、'Media'）。
        count: The maximum number of tweets to retrieve.
               取得するツイートの最大数。

    Returns:
        List[Tweet]: A list of Tweet objects representing the fetched tweets.
                     取得されたツイートを表すTweetオブジェクトのリスト。

    Raises:
        ValueError: If neither `user_id` nor `screen_name` is provided.
                    `user_id`も`screen_name`も提供されない場合。
        Exception: If any error occurs during the tweet fetching process.
                   ツイート取得プロセス中にエラーが発生した場合。
    """
    if not user_id and not screen_name:
        raise ValueError("Either user_id or screen_name must be provided")

    try:
        # If only screen_name is provided, first retrieve the user's ID.
        # screen_nameのみが提供されている場合、まずユーザーのIDを取得します。
        if not user_id and screen_name:
            user = await client.get_user_by_screen_name(screen_name)
            user_id = user.id

        # Fetch the user's tweets based on the specified type and count.
        # 指定されたタイプと数に基づいてユーザーのツイートを取得します。
        tweets = await client.get_user_tweets(str(user_id), tweet_type, count=count)
        return tweets

    except Exception as e:
        # Log the error and re-raise it for higher-level handling.
        # エラーをログに記録し、上位レベルでの処理のために再発生させます。
        if settings:
            print(settings.lang_data.get("twitter_error_getting_rss_tweets", "Error getting RSS-like tweets: {0}").format(str(e)))
        else:
            print(f"Error getting RSS-like tweets: {str(e)}")
        raise

# Convenience functions that use the client manager
# クライアントマネージャーを使用するコンビニエンス関数

async def analyze_tweet_with_manager(client_manager: TwitterClientManager, tweet_id: str) -> Dict[str, Any]:
    """
    Analyzes a tweet using the `TwitterClientManager` to automatically handle client selection and fallback.

    `TwitterClientManager`を使用してツイートを分析し、クライアントの自動選択とフォールバックを処理します。

    Args:
        client_manager: An instance of `TwitterClientManager`.
                        `TwitterClientManager`のインスタンス。
        tweet_id: The ID of the tweet to analyze.
                  分析するツイートのID。

    Returns:
        Dict[str, Any]: A dictionary containing the analysis results.
                        分析結果を含む辞書。
    """
    return await client_manager.execute_with_fallback(analyze_tweet, tweet_id)

async def get_tweet_thread_with_manager(client_manager: TwitterClientManager, tweet_id: str) -> List[Tweet]:
    """
    Retrieves a tweet thread using the `TwitterClientManager` for automatic client selection and fallback.

    `TwitterClientManager`を使用してツイートスレッドを取得し、クライアントの自動選択とフォールバックを処理します。

    Args:
        client_manager: An instance of `TwitterClientManager`.
                        `TwitterClientManager`のインスタンス。
        tweet_id: The ID of the tweet for which to retrieve the thread.
                  スレッドを取得するツイートのID。

    Returns:
        List[Tweet]: A list of `Tweet` objects representing the thread.
                     スレッドを表す`Tweet`オブジェクトのリスト。
    """
    return await client_manager.execute_with_fallback(get_tweet_thread, tweet_id, client_manager.settings)

async def get_rss_like_tweets_with_manager(client_manager: TwitterClientManager, user_id: Optional[str] = None, 
                                          screen_name: Optional[str] = None, tweet_type: str = 'Tweets', count: int = 10) -> List[Tweet]:
    """
    Fetches RSS-like tweets using the `TwitterClientManager`. This operation always uses
    the authenticated client managed by `TwitterClientManager`.

    `TwitterClientManager`を使用してRSSのようなツイートを取得します。この操作は常に
    `TwitterClientManager`によって管理される認証済みクライアントを使用します。

    Args:
        client_manager: An instance of `TwitterClientManager`.
                        `TwitterClientManager`のインスタンス。
        user_id: The ID of the user to get tweets from. Required if `screen_name` is not provided.
                 ツイートを取得するユーザーのID。`screen_name`が提供されない場合は必須。
        screen_name: The screen name of the user to get tweets from. Required if `user_id` is not provided.
                     ツイートを取得するユーザーのスクリーン名。`user_id`が提供されない場合は必須。
        tweet_type: The type of tweets to retrieve (e.g., 'Tweets', 'Replies', 'Media').
                    ツイートの種類（例: 'Tweets'、'Replies'、'Media'）。
        count: The maximum number of tweets to retrieve.
               取得するツイートの最大数。

    Returns:
        List[Tweet]: A list of `Tweet` objects representing the fetched tweets.
                     取得されたツイートを表す`Tweet`オブジェクトのリスト。
    """
    client = await client_manager.get_rss_client()
    return await get_rss_like_tweets(client, user_id, screen_name, tweet_type, count, client_manager.settings)
