

TwikitライブラリのGuestClientを使用してゲストでツイートを取得する方法をご説明します。

## GuestClientの基本的な使用方法

TwikitにはGuestClientという機能があり、認証なしでTwitterの公開データにアクセスできます。 [1](#1-0)

### 1. GuestClientの初期化とアクティベーション

まず、GuestClientを初期化し、`activate()`メソッドでゲストトークンを取得する必要があります：

```python
from twikit.guest import GuestClient

client = GuestClient()
await client.activate()  # ゲストトークンを取得
``` [1](#1-0) 

### 2. ユーザーのツイートを取得

ユーザーのツイートを取得するには、まずユーザー情報を取得してからツイートを取得します：

```python
# ユーザー名からユーザー情報を取得
user = await client.get_user_by_screen_name('example_user')

# そのユーザーのツイートを取得
tweets = await client.get_user_tweets(user.id)
for tweet in tweets:
    print(tweet.text)
``` [2](#1-1) [3](#1-2) 

### 3. 特定のツイートを取得

ツイートIDが分かっている場合は、直接そのツイートを取得できます：

```python
tweet = await client.get_tweet_by_id('1234567890')
print(tweet.text)
```

### 4. ゲスト用Tweetオブジェクト

GuestClientで取得されるTweetオブジェクトには、以下のような情報が含まれています： [4](#1-3)

- `id`: ツイートID
- `text`: ツイート本文
- `user`: 投稿者情報
- `created_at`: 投稿日時
- `media`: 添付メディア
- `favorite_count`: いいね数
- `retweet_count`: リツイート数
- `reply_count`: 返信数

## 完全な使用例

```python
import asyncio
from twikit.guest import GuestClient

async def main():
    client = GuestClient()
    await client.activate()
    
    # ユーザーのツイートを取得
    user = await client.get_user_by_screen_name('example_user')
    tweets = await client.get_user_tweets(user.id, count=10)
    
    for tweet in tweets:
        print(f"ツイート: {tweet.text}")
        print(f"投稿者: {tweet.user.screen_name}")
        print(f"いいね数: {tweet.favorite_count}")
        print("---")

asyncio.run(main())
```

## Notes

GuestClientは読み取り専用のアクセスを提供し、ツイートの投稿やいいね、リツイートなどの操作はできません。また、通常の認証されたクライアントと比べて、取得できるデータに制限がある場合があります。TwitterのAPI仕様変更により、ゲストアクセスの可用性は変更される可能性があります。

Wiki pages you might want to explore:
- [User Operations (d60/twikit)](/wiki/d60/twikit#2.3)
- [Media Operations (d60/twikit)](/wiki/d60/twikit#2.4)
- [Guest Client (d60/twikit)](/wiki/d60/twikit#3.2)
- 
Based on the twikit library documentation and source code, the `Tweet` object retrieved using the `GuestClient` contains the following attributes:

## Core Identifiers
- `id` - The unique identifier of the tweet
- `created_at` - The creation timestamp as a string
- `created_at_datetime` - The creation timestamp as a datetime object

## Content Properties
- `text` - The tweet text content
- `full_text` - The full text of the tweet
- `lang` - The language of the tweet
- `hashtags` - List of hashtags in the tweet
- `urls` - List of URLs in the tweet

## Relationship Properties
- `in_reply_to` - ID of the tweet this is replying to
- `quote` - The quoted tweet object (if any)
- `retweeted_tweet` - The original tweet if this is a retweet
- `reply_to` - List of tweets this is replying to
- `thread` - List of tweets in the thread

## Engagement Metrics
- `reply_count` - Number of replies
- `favorite_count` - Number of likes/favorites
- `retweet_count` - Number of retweets
- `bookmark_count` - Number of bookmarks
- `view_count` - Number of views
- `quote_count` - Number of quote tweets

## State Properties
- `favorited` - Whether the tweet is favorited
- `bookmarked` - Whether the tweet is bookmarked
- `possibly_sensitive` - Whether the tweet is marked as sensitive

## Media & Attachments
- `media` - List of media objects (photos, videos, etc.)
- `poll` - Poll object if the tweet contains a poll
- `has_card` - Whether the tweet has a card attachment
- `thumbnail_title` - Title of the thumbnail
- `thumbnail_url` - URL of the thumbnail

## Editing Properties
- `is_edit_eligible` - Whether the tweet can be edited
- `edits_remaining` - Number of edits remaining
- `editable_until_msecs` - Timestamp until when the tweet can be edited

## Community Features
- `has_community_notes` - Whether the tweet has community notes
- `community_note` - Community note object if present

## Location
- `place` - Location information if available

## User Information
- `user` - The User object representing the tweet author [1](#2-0)

## Notes

The guest implementation of the Tweet class provides read-only access to tweet data without authentication. Unlike the authenticated version, guest tweets cannot perform interactive actions like favoriting, retweeting, or replying. [1](#2-0)

The guest Tweet class has direct property access rather than property methods for many attributes, making it simpler but more limited than the authenticated version. [1](#2-0) 
