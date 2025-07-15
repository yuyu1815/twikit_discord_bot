import asyncio
from typing import Dict, List, Any, Optional, Union

from twikit.tweet import Tweet
from twikit import Client
from twikit.guest import GuestClient

from .twitter_client_manager import TwitterClientManager

async def get_tweet_thread(client: Union[GuestClient, Client], tweet_id: str) -> List[Tweet]:
    """
    Get the thread of tweets that a reply tweet belongs to.
    返信ツイートが属するツイートのスレッドを取得します。

    Args:
        client: A twikit client instance (guest or authenticated)
        client: twikit クライアントインスタンス (ゲストまたは認証済み)
        tweet_id: The ID of the tweet to get the thread for
        tweet_id: スレッドを取得するツイートのID

    Returns:
        A list of Tweet objects representing the thread, ordered from oldest to newest
        スレッドを表すTweetオブジェクトのリスト。古いものから新しいものへ順序付けられています。
    """
    thread = []
    current_tweet_id = tweet_id

    while current_tweet_id:
        try:
            tweet = await client.get_tweet_by_id(str(current_tweet_id))
            if tweet is None:
                break

            thread.insert(0, tweet)  # Insert at the beginning to maintain oldest-to-newest order
            current_tweet_id = tweet.in_reply_to
        except Exception:
            # If we encounter an error, return what we've collected so far
            break

    return thread

async def analyze_tweet(client: Union[GuestClient, Client], tweet_id: str) -> Dict[str, Any]:
    """
    Analyze a tweet to determine its type (retweet, reply, or normal) and extract relevant information.

    Args:
        client: A twikit client instance (guest or authenticated)
        tweet_id: The ID of the tweet to analyze

    Returns:
        A dictionary containing the analysis results
    """
    result = {
        "tweet_id": tweet_id,
        "type": "unknown",  # Default type
    }

    try:
        # Get the tweet
        tweet = await client.get_tweet_by_id(str(tweet_id))

        if tweet is None:
            result["error"] = "Tweet not found"
            return result

        # Add basic tweet data
        result["tweet_data"] = {
            "id": tweet.id,
            "user_screen_name": tweet.user.screen_name,
            "text": tweet.text
        }

        # Check if it's a retweet
        if hasattr(tweet, 'retweeted_tweet') and tweet.retweeted_tweet:
            result["type"] = "retweet"
            result["original_tweet"] = {
                "id": tweet.retweeted_tweet.id,
                "user_screen_name": tweet.retweeted_tweet.user.screen_name,
                "text": tweet.retweeted_tweet.text
            }
            return result

        # Check if it's a reply
        if tweet.in_reply_to:
            result["type"] = "reply"
            # Get the thread
            thread = await get_tweet_thread(client, tweet_id)

            # Format the thread data
            result["reply_thread"] = []
            for t in thread:
                result["reply_thread"].append({
                    "id": t.id,
                    "user_screen_name": t.user.screen_name,
                    "text": t.text
                })
            return result

        # If it's neither a retweet nor a reply, it's a normal tweet
        result["type"] = "normal"
        return result

    except Exception as e:
        result["error"] = str(e)
        return result

async def get_rss_like_tweets(client: Client, user_id: Optional[str] = None, screen_name: Optional[str] = None, tweet_type: str = 'Tweets', count: int = 10) -> List[Tweet]:
    """
    Get the latest tweets from a user, similar to an RSS feed.

    Args:
        client: An authenticated twikit Client instance
        user_id: The ID of the user to get tweets from (optional if screen_name is provided)
        screen_name: The screen name of the user to get tweets from (optional if user_id is provided)
        tweet_type: The type of tweets to retrieve ('Tweets', 'Replies', 'Media', etc.) (default: 'Tweets')
        count: The number of tweets to retrieve (default: 10)

    Returns:
        A list of Tweet objects

    Raises:
        ValueError: If neither user_id nor screen_name is provided
    """
    if not user_id and not screen_name:
        raise ValueError("Either user_id or screen_name must be provided")

    try:
        # If only screen_name is provided, get the user ID first
        if not user_id and screen_name:
            user = await client.get_user_by_screen_name(screen_name)
            user_id = user.id

        # Get the user's tweets
        tweets = await client.get_user_tweets(str(user_id), tweet_type, count=count)
        return tweets

    except Exception as e:
        # Log the error and re-raise
        print(f"Error getting RSS-like tweets: {str(e)}")
        raise

# Convenience functions that use the client manager

async def analyze_tweet_with_manager(client_manager: TwitterClientManager, tweet_id: str) -> Dict[str, Any]:
    """
    Analyze a tweet using the client manager for automatic client selection and fallback.

    Args:
        client_manager: A TwitterClientManager instance
        tweet_id: The ID of the tweet to analyze

    Returns:
        A dictionary containing the analysis results
    """
    return await client_manager.execute_with_fallback(analyze_tweet, tweet_id)

async def get_tweet_thread_with_manager(client_manager: TwitterClientManager, tweet_id: str) -> List[Tweet]:
    """
    Get a tweet thread using the client manager for automatic client selection and fallback.

    Args:
        client_manager: A TwitterClientManager instance
        tweet_id: The ID of the tweet to get the thread for

    Returns:
        A list of Tweet objects representing the thread
    """
    return await client_manager.execute_with_fallback(get_tweet_thread, tweet_id)

async def get_rss_like_tweets_with_manager(client_manager: TwitterClientManager, user_id: Optional[str] = None, 
                                          screen_name: Optional[str] = None, tweet_type: str = 'Tweets', count: int = 10) -> List[Tweet]:
    """
    Get RSS-like tweets using the client manager (always uses authenticated client).

    Args:
        client_manager: A TwitterClientManager instance
        user_id: The ID of the user to get tweets from (optional if screen_name is provided)
        screen_name: The screen name of the user to get tweets from (optional if user_id is provided)
        tweet_type: The type of tweets to retrieve ('Tweets', 'Replies', 'Media', etc.) (default: 'Tweets')
        count: The number of tweets to retrieve (default: 10)

    Returns:
        A list of Tweet objects
    """
    client = await client_manager.get_rss_client()
    return await get_rss_like_tweets(client, user_id, screen_name, tweet_type, count)
