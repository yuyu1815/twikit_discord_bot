# Core Directory / Coreディレクトリ

## Overview / 概要

This directory contains the core functionality and business logic of the Twikit Discord Bot. It includes the main bot class, Twitter integration, database operations, and tweet analysis components.

このディレクトリには、Twikit Discord Botのコア機能とビジネスロジックが含まれています。メインのbotクラス、Twitter統合、データベース操作、ツイート分析コンポーネントが含まれます。

## Files / ファイル

### bot.py
Contains the main `TwikitBot` class that serves as the Discord bot's core controller.

Discordボットのコアコントローラーとして機能するメイン `TwikitBot` クラスが含まれています。

**Key Features / 主な機能:**
- Bot initialization and setup / Bot初期化とセットアップ
- Event handling and lifecycle management / イベント処理とライフサイクル管理
- Cog loading and management / Cog読み込みと管理
- Discord client integration / Discordクライアント統合

### database.py
Handles all database operations using SQLite for persistent data storage.

永続的なデータストレージのためにSQLiteを使用してすべてのデータベース操作を処理します。

**Key Features / 主な機能:**
- Guild configuration storage / ギルド設定ストレージ
- Twitter message tracking / Twitterメッセージ追跡
- Database schema management / データベーススキーマ管理
- Data migration and cleanup / データ移行とクリーンアップ

### twitter_analyzer.py
Implements tweet analysis and thread retrieval functionality.

ツイート分析とスレッド取得機能を実装します。

**Key Features / 主な機能:**
- **Tweet Type Analysis** / **ツイートタイプ分析**: Determines if a tweet is normal, retweet, or reply / ツイートが通常、リツイート、返信かを判定
- **Thread Retrieval** / **スレッド取得**: For reply tweets, retrieves the entire conversation thread / 返信ツイートの場合、会話スレッド全体を取得
- **RSS-like Functionality** / **RSS風機能**: Fetches latest tweets from users similar to RSS feeds / RSSフィードのようにユーザーから最新ツイートを取得
- **Error Handling** / **エラーハンドリング**: Comprehensive error handling for Twitter API issues / Twitter API問題の包括的なエラーハンドリング

### twitter_client.py
Handles Twitter API communication and authentication.

Twitter API通信と認証を処理します。

**Key Features / 主な機能:**
- Twitter API integration / Twitter API統合
- Cookie-based authentication / クッキーベース認証
- Rate limit handling / レート制限処理
- Tweet fetching and parsing / ツイート取得と解析

### twitter_client_manager.py
Manages both guest and authenticated Twitter clients for optimal performance.

最適なパフォーマンスのためにゲストと認証済みTwitterクライアントの両方を管理します。

**Key Features / 主な機能:**
- **Dual Client Management** / **デュアルクライアント管理**: Manages both guest and authenticated clients / ゲストと認証済みクライアントの両方を管理
- **Automatic Fallback** / **自動フォールバック**: Falls back to guest client when authenticated client fails / 認証済みクライアントが失敗した場合にゲストクライアントにフォールバック
- **Performance Optimization** / **パフォーマンス最適化**: Optimizes API usage and reduces rate limiting / API使用を最適化し、レート制限を削減
- **Client Health Monitoring** / **クライアント健全性監視**: Monitors client status and handles reconnections / クライアントステータスを監視し、再接続を処理

## Architecture / アーキテクチャ

The core components follow a layered architecture:

コアコンポーネントは階層アーキテクチャに従います：

```
┌─────────────────┐
│     bot.py      │  ← Main bot controller / メインbotコントローラー
├─────────────────┤
│ twitter_client_ │  ← Client management layer / クライアント管理層
│    manager.py   │
├─────────────────┤
│twitter_client.py│  ← Twitter API layer / Twitter API層
├─────────────────┤
│twitter_analyzer │  ← Analysis logic layer / 分析ロジック層
│     .py         │
├─────────────────┤
│   database.py   │  ← Data persistence layer / データ永続化層
└─────────────────┘
```

## Key Functions / 主要関数

### twitter_analyzer.py Functions / twitter_analyzer.py関数

#### Main Functions / メイン関数
- `get_rss_like_tweets_with_manager(manager, screen_name, count)` - Fetch latest tweets RSS-style / RSS風に最新ツイートを取得
- `analyze_tweet_with_manager(manager, tweet_url)` - Analyze a specific tweet / 特定のツイートを分析

#### Analysis Functions / 分析関数
- `analyze_tweet_type(tweet)` - Determine tweet type (normal/retweet/reply) / ツイートタイプを判定（通常/リツイート/返信）
- `get_conversation_thread(client, tweet_id)` - Retrieve conversation thread / 会話スレッドを取得
- `format_analysis_result(tweet, tweet_type, thread_tweets)` - Format analysis results / 分析結果をフォーマット

## Data Structures / データ構造

### Tweet Analysis Result / ツイート分析結果
```python
{
    "success": bool,                    # Analysis success status / 分析成功ステータス
    "tweet_type": str,                  # "normal", "retweet", or "reply" / "normal"、"retweet"、または"reply"
    "original_tweet": Tweet,            # Original tweet object / 元のツイートオブジェクト
    "thread_tweets": List[Tweet],       # Thread tweets (for replies) / スレッドツイート（返信用）
    "error": str,                       # Error message if failed / 失敗時のエラーメッセージ
    "analysis_time": str                # Analysis timestamp / 分析タイムスタンプ
}
```

## Dependencies / 依存関係

- `twikit` - Twitter API client library / Twitter APIクライアントライブラリ
- `sqlite3` - Database operations / データベース操作
- `discord.py` - Discord bot framework / Discord botフレームワーク
- `asyncio` - Asynchronous programming / 非同期プログラミング
- `json` - JSON data processing / JSONデータ処理
- `datetime` - Date and time handling / 日時処理

## Error Handling / エラーハンドリング

The core modules implement comprehensive error handling:

コアモジュールは包括的なエラーハンドリングを実装します：

- **Twitter API Errors** / **Twitter APIエラー**: Rate limits, authentication failures / レート制限、認証失敗
- **Network Errors** / **ネットワークエラー**: Connection timeouts, network unavailability / 接続タイムアウト、ネットワーク利用不可
- **Database Errors** / **データベースエラー**: Connection issues, schema problems / 接続問題、スキーマ問題
- **Parsing Errors** / **解析エラー**: Invalid tweet data, malformed responses / 無効なツイートデータ、不正な形式の応答

## Usage Examples / 使用例

### Tweet Analysis / ツイート分析
```python
from src.core.twitter_analyzer import analyze_tweet_with_manager
from src.core.twitter_client_manager import TwitterClientManager

manager = TwitterClientManager()
result = await analyze_tweet_with_manager(manager, "https://twitter.com/user/status/123456789")

if result["success"]:
    print(f"Tweet type: {result['tweet_type']}")
    if result["thread_tweets"]:
        print(f"Thread contains {len(result['thread_tweets'])} tweets")
```

### RSS-like Tweet Fetching / RSS風ツイート取得
```python
from src.core.twitter_analyzer import get_rss_like_tweets_with_manager

tweets = await get_rss_like_tweets_with_manager(manager, "username", count=10)
for tweet in tweets:
    print(f"Tweet: {tweet.text}")
```

## Performance Considerations / パフォーマンス考慮事項

- **Client Pooling** / **クライアントプーリング**: Reuses Twitter clients to reduce overhead / オーバーヘッドを削減するためにTwitterクライアントを再利用
- **Caching** / **キャッシュ**: Caches frequently accessed data / 頻繁にアクセスされるデータをキャッシュ
- **Rate Limiting** / **レート制限**: Implements intelligent rate limiting to avoid API restrictions / API制限を回避するためのインテリジェントなレート制限を実装
- **Asynchronous Operations** / **非同期操作**: Uses async/await for non-blocking operations / ノンブロッキング操作にasync/awaitを使用