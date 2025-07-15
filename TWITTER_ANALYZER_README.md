# Twitter Analyzer Module

This document describes the implementation of the Twitter tweet analysis and reply tree expansion module as specified in the technical requirements.

## Overview

The implementation consists of two main components:

1. **TwitterClientManager** (`src/core/twitter_client_manager.py`): Manages both guest and authenticated Twitter clients, providing appropriate clients based on the operation type.

2. **Twitter Analyzer** (`src/core/twitter_analyzer.py`): Implements the core functionality for tweet analysis, thread retrieval, and RSS-like tweet fetching.

## Features

### 1. Tweet Analysis

The module can analyze tweets to determine their type:
- Normal tweets
- Retweets (with original tweet information)
- Reply tweets (with the entire conversation thread)

### 2. Reply Thread Expansion

For reply tweets, the module can retrieve the entire conversation thread, from the original tweet to the current reply.

### 3. RSS-like Tweet Fetching

The module can fetch the latest tweets from a user, similar to an RSS feed.

## Components

### TwitterClientManager

The `TwitterClientManager` class manages both guest and authenticated Twitter clients:

- **Guest Client**: Used primarily for tweet analysis operations
- **Authenticated Client**: Used for RSS-like operations and as a fallback for tweet analysis

Key features:
- Client initialization and activation
- Client selection based on operation type
- Rate limit handling and tracking
- Automatic fallback between clients

### Twitter Analyzer

The Twitter Analyzer module provides the following functions:

1. `get_tweet_thread(client, tweet_id)`: Retrieves the thread of tweets that a reply tweet belongs to.

2. `analyze_tweet(client, tweet_id)`: Analyzes a tweet to determine its type and extract relevant information.

3. `get_rss_like_tweets(client, user_id, screen_name, count)`: Gets the latest tweets from a user.

Additionally, convenience functions are provided that use the `TwitterClientManager` for automatic client selection and fallback:

1. `analyze_tweet_with_manager(client_manager, tweet_id)`
2. `get_tweet_thread_with_manager(client_manager, tweet_id)`
3. `get_rss_like_tweets_with_manager(client_manager, user_id, screen_name, count)`

## Usage

### Initialization

```python
from src.core.twitter_client_manager import TwitterClientManager

# Initialize the client manager
client_manager = TwitterClientManager()
await client_manager.initialize()
```

### Tweet Analysis

```python
from src.core.twitter_analyzer import analyze_tweet_with_manager

# Analyze a tweet
result = await analyze_tweet_with_manager(client_manager, "1234567890")

# Check the tweet type
if result["type"] == "retweet":
    # Handle retweet
    original_tweet = result["original_tweet"]
    print(f"Original tweet by @{original_tweet['user_screen_name']}")
    
elif result["type"] == "reply":
    # Handle reply
    reply_thread = result["reply_thread"]
    print(f"Reply thread length: {len(reply_thread)}")
    
else:
    # Handle normal tweet
    print("Normal tweet")
```

### Thread Retrieval

```python
from src.core.twitter_analyzer import get_tweet_thread_with_manager

# Get a tweet thread
thread = await get_tweet_thread_with_manager(client_manager, "1234567890")

# Process the thread
for i, tweet in enumerate(thread):
    print(f"[{i+1}] @{tweet.user.screen_name}: {tweet.text}")
```

### RSS-like Tweet Fetching

```python
from src.core.twitter_analyzer import get_rss_like_tweets_with_manager

# Get the latest tweets from a user
tweets = await get_rss_like_tweets_with_manager(
    client_manager, 
    screen_name="example_user",
    count=10
)

# Process the tweets
for tweet in tweets:
    print(f"{tweet.created_at}: {tweet.text}")
```

## Error Handling

The module includes comprehensive error handling:

- Rate limit detection and handling
- Authentication error handling
- Automatic client fallback
- Structured error information in the analysis results

## Testing

A test script (`test_twitter_analyzer.py`) is provided to verify the implementation. It tests:

1. Tweet analysis with different types of tweets
2. Thread retrieval with a reply tweet
3. RSS-like tweet fetching with a user

To run the tests:

```
python test_twitter_analyzer.py
```

## Implementation Notes

- The implementation follows the specified requirements, prioritizing the guest client for tweet analysis operations and using the authenticated client for RSS-like operations.
- The module is designed to be easily integrated into the main system.
- The code includes comprehensive error handling and client switching logic.
- Type hints are used throughout the code to improve maintainability.