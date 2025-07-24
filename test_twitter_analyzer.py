import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.twitter_client_manager import TwitterClientManager
from src.core.twitter_analyzer import (
    analyze_tweet_with_manager,
    get_tweet_thread_with_manager,
    get_latest_tweets_with_manager
)

# Test tweet IDs (same as in test_parent_tweet.py)
PARENT_TWEET_ID = "1944401404816200173"
REPLY_TWEET_ID = "1944402996160540687"
RETWEET_ID = "1924465040759087252"

# Test user
TEST_USER_SCREEN_NAME = "X"

async def test_analyze_tweet(client_manager, tweet_id, expected_type):
    """Test the analyze_tweet function with a specific tweet ID."""
    print(f"\n--- Testing analyze_tweet with tweet ID: {tweet_id} ---")
    try:
        result = await analyze_tweet_with_manager(client_manager, tweet_id)
        print(f"Tweet type: {result['type']}")
        
        if result['type'] != expected_type:
            print(f"WARNING: Expected type '{expected_type}' but got '{result['type']}'")
        
        # Print additional details based on tweet type
        if result['type'] == 'retweet' and 'original_tweet' in result:
            print(f"Original tweet by: @{result['original_tweet']['user_screen_name']}")
            print(f"Original tweet text: {result['original_tweet']['text'][:100]}...")
        
        elif result['type'] == 'reply' and 'reply_thread' in result:
            print(f"Reply thread length: {len(result['reply_thread'])}")
            for i, tweet in enumerate(result['reply_thread']):
                print(f"  [{i+1}] @{tweet['user_screen_name']}: {tweet['text'][:50]}...")
        
        return result
    except Exception as e:
        print(f"Error in analyze_tweet: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_get_tweet_thread(client_manager, tweet_id):
    """Test the get_tweet_thread function with a specific tweet ID."""
    print(f"\n--- Testing get_tweet_thread with tweet ID: {tweet_id} ---")
    try:
        thread = await get_tweet_thread_with_manager(client_manager, tweet_id)
        print(f"Thread length: {len(thread)}")
        for i, tweet in enumerate(thread):
            print(f"  [{i+1}] @{tweet.user.screen_name}: {tweet.text[:50]}...")
        return thread
    except Exception as e:
        print(f"Error in get_tweet_thread: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_get_latest_tweets(client_manager, screen_name, count=5):
    """Test the get_latest_tweets function with a specific user."""
    print(f"\n--- Testing get_latest_tweets with user: {screen_name} ---")
    try:
        tweets = await get_latest_tweets_with_manager(client_manager, screen_name=screen_name, count=count)
        print(f"Retrieved {len(tweets)} tweets")
        for i, tweet in enumerate(tweets):
            print(f"  [{i+1}] {tweet.created_at}: {tweet.text[:50]}...")
        return tweets
    except Exception as e:
        print(f"Error in get_latest_tweets: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function."""
    print("Initializing Twitter client manager...")
    client_manager = TwitterClientManager()
    
    # Initialize the client manager
    success = await client_manager.initialize()
    if not success:
        print("Failed to initialize any Twitter clients. Exiting.")
        return
    
    print("Client manager initialized successfully.")
    
    # Test analyze_tweet with different types of tweets
    await test_analyze_tweet(client_manager, PARENT_TWEET_ID, "normal")
    await test_analyze_tweet(client_manager, REPLY_TWEET_ID, "reply")
    await test_analyze_tweet(client_manager, RETWEET_ID, "retweet")
    
    # Test get_tweet_thread with a reply tweet
    await test_get_tweet_thread(client_manager, REPLY_TWEET_ID)
    
    # Test get_latest_tweets with a user
    try:
        await test_get_latest_tweets(client_manager, TEST_USER_SCREEN_NAME)
    except RuntimeError as e:
        print(f"Latest tweets test failed (expected if no auth client available): {e}")
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    # Set the event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the main function
    asyncio.run(main())