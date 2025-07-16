# twikit 仕様書

## 概要

twikitは、Twitter API v2を使用してTwitterとやり取りするための非公式Pythonライブラリです。公式のTwitter APIクライアントよりも簡単で直感的なインターフェースを提供し、ツイートの取得、投稿、ユーザー情報の取得などの機能を提供します。

### 基本情報
- **ライブラリ名**: twikit
- **開発者**: d60/twikit community
- **Context7対応**: 非対応
- **公式リポジトリ**: https://github.com/d60/twikit
- **ライセンス**: MIT License

## インストール

```bash
pip install twikit
```

### 必要な依存関係
- Python 3.7以上
- httpx
- fake-useragent

## 主な機能

### 1. ツイート操作
- ツイートの取得
- ツイートの投稿
- ツイートの削除
- リツイート・いいね

### 2. ユーザー操作
- ユーザー情報の取得
- フォロー・アンフォロー
- ユーザーのツイート履歴取得

### 3. 検索機能
- ツイート検索
- ユーザー検索
- トレンド取得

### 4. 認証機能
- Cookie認証
- ゲストアクセス
- 複数アカウント対応

## 基本的な使用方法

### クライアントの初期化

```python
from twikit import Client

# クライアントの作成
client = Client('ja-JP')  # 言語設定（オプション）

# ゲストとしてアクティベート（認証不要）
await client.activate()
```

### 認証済みクライアントの使用

```python
from twikit import Client

client = Client('ja-JP')

# ユーザー名とパスワードでログイン
await client.login(
    auth_info_1='username_or_email',
    auth_info_2='username_or_phone',
    password='your_password'
)

# またはCookieファイルから読み込み
client.load_cookies('cookies.json')
```

### ツイートの取得

```python
from twikit import Client

client = Client()
await client.activate()

# ツイートIDから取得
tweet_id = '1234567890123456789'
tweet = await client.get_tweet_by_id(tweet_id)

print(f'ツイート内容: {tweet.text}')
print(f'投稿者: {tweet.user.name}')
print(f'いいね数: {tweet.favorite_count}')
print(f'リツイート数: {tweet.retweet_count}')
```

### ユーザー情報の取得

```python
# ユーザー名から取得
user = await client.get_user_by_screen_name('twitter')

print(f'ユーザー名: {user.name}')
print(f'スクリーン名: {user.screen_name}')
print(f'フォロワー数: {user.followers_count}')
print(f'フォロー数: {user.friends_count}')
print(f'プロフィール: {user.description}')
```

## 主要クラスとメソッド

### Client クラス

#### 初期化
```python
client = Client(language='ja-JP')
```

#### 認証メソッド
- `activate()`: ゲストとしてアクティベート
- `login()`: ユーザー名/パスワードでログイン
- `load_cookies()`: Cookieファイルから認証情報を読み込み
- `save_cookies()`: 認証情報をCookieファイルに保存

#### ツイート関連メソッド
- `get_tweet_by_id(tweet_id)`: ツイートIDからツイートを取得
- `get_user_tweets(user_id, tweet_type, count)`: ユーザーのツイートを取得
- `create_tweet(text)`: ツイートを投稿
- `delete_tweet(tweet_id)`: ツイートを削除

#### ユーザー関連メソッド
- `get_user_by_screen_name(screen_name)`: スクリーン名からユーザーを取得
- `get_user_by_id(user_id)`: ユーザーIDからユーザーを取得
- `follow_user(user_id)`: ユーザーをフォロー
- `unfollow_user(user_id)`: ユーザーをアンフォロー

#### 検索メソッド
- `search_tweet(query, product)`: ツイートを検索
- `search_user(query)`: ユーザーを検索

### Tweet クラス

#### 主要属性
- `id`: ツイートID
- `text`: ツイート内容
- `user`: 投稿者のUserオブジェクト
- `created_at`: 投稿日時
- `favorite_count`: いいね数
- `retweet_count`: リツイート数
- `reply_count`: 返信数
- `is_quote_status`: 引用ツイートかどうか
- `retweeted_tweet`: リツイート元のツイート

#### 主要メソッド
- `reply(text)`: このツイートに返信
- `retweet()`: このツイートをリツイート
- `unretweet()`: リツイートを取り消し
- `favorite()`: このツイートにいいね
- `unfavorite()`: いいねを取り消し

### User クラス

#### 主要属性
- `id`: ユーザーID
- `name`: 表示名
- `screen_name`: スクリーン名（@以降）
- `description`: プロフィール
- `followers_count`: フォロワー数
- `friends_count`: フォロー数
- `statuses_count`: ツイート数
- `profile_image_url`: プロフィール画像URL
- `verified`: 認証済みかどうか

#### 主要メソッド
- `follow()`: このユーザーをフォロー
- `unfollow()`: このユーザーをアンフォロー
- `get_tweets(tweet_type, count)`: このユーザーのツイートを取得

## 高度な使用方法

### ユーザーのツイート履歴取得

```python
from twikit import Client

client = Client()
await client.activate()

# ユーザーを取得
user = await client.get_user_by_screen_name('twitter')

# ユーザーのツイートを取得
tweets = await client.get_user_tweets(user.id, 'Tweets', count=20)

for tweet in tweets:
    print(f'{tweet.created_at}: {tweet.text}')
    print(f'いいね: {tweet.favorite_count}, RT: {tweet.retweet_count}')
    print('-' * 50)
```

### ツイート検索

```python
from twikit import Client

client = Client()
await client.activate()

# キーワードでツイートを検索
search_results = await client.search_tweet('Python プログラミング', product='Latest')

for tweet in search_results:
    print(f'@{tweet.user.screen_name}: {tweet.text}')
    print(f'投稿日時: {tweet.created_at}')
    print('-' * 50)
```

### 認証済みクライアントでのツイート投稿

```python
from twikit import Client

client = Client()

# ログイン
await client.login(
    auth_info_1='your_username',
    auth_info_2='your_email',
    password='your_password'
)

# ツイートを投稿
tweet = await client.create_tweet('Hello, Twitter! #twikit')
print(f'ツイートが投稿されました: {tweet.id}')

# Cookieを保存（次回ログイン時に使用）
client.save_cookies('cookies.json')
```

### リツイートといいね

```python
from twikit import Client

client = Client()
client.load_cookies('cookies.json')

# ツイートを取得
tweet = await client.get_tweet_by_id('1234567890123456789')

# いいね
await tweet.favorite()
print('いいねしました')

# リツイート
await tweet.retweet()
print('リツイートしました')

# 返信
reply = await tweet.reply('素晴らしいツイートですね！')
print(f'返信しました: {reply.id}')
```

### フォロー・アンフォロー

```python
from twikit import Client

client = Client()
client.load_cookies('cookies.json')

# ユーザーを取得
user = await client.get_user_by_screen_name('target_user')

# フォロー
await user.follow()
print(f'{user.name}をフォローしました')

# アンフォロー
await user.unfollow()
print(f'{user.name}をアンフォローしました')
```

## Cookie管理

### Cookieの保存と読み込み

```python
from twikit import Client

client = Client()

# 初回ログイン
await client.login(
    auth_info_1='username',
    auth_info_2='email',
    password='password'
)

# Cookieを保存
client.save_cookies('twitter_cookies.json')

# 次回以降はCookieから読み込み
client_new = Client()
client_new.load_cookies('twitter_cookies.json')
```

### Cookie形式の変換

```python
import json
from twikit import Client

# ブラウザのCookieをtwikit形式に変換
def convert_browser_cookies_to_twikit(browser_cookies):
    """
    ブラウザのCookie配列をtwikit形式の辞書に変換
    """
    twikit_cookies = {}
    for cookie in browser_cookies:
        name = cookie.get('name')
        value = cookie.get('value')
        if name and value:
            twikit_cookies[name] = value
    return twikit_cookies

# 使用例
browser_cookies = [
    {'name': 'auth_token', 'value': 'abc123'},
    {'name': 'ct0', 'value': 'def456'},
    # ... その他のCookie
]

twikit_cookies = convert_browser_cookies_to_twikit(browser_cookies)

# JSONファイルに保存
with open('cookies.json', 'w') as f:
    json.dump(twikit_cookies, f, indent=2)

# twikitで読み込み
client = Client()
client.load_cookies('cookies.json')
```

## エラーハンドリング

### 一般的な例外処理

```python
from twikit import Client
from twikit.errors import TwikitException, Unauthorized, TooManyRequests

client = Client()

try:
    await client.activate()
    tweet = await client.get_tweet_by_id('invalid_id')
    
except Unauthorized:
    print('認証が必要です')
except TooManyRequests:
    print('レート制限に達しました。しばらく待ってから再試行してください')
except TwikitException as e:
    print(f'Twikitエラー: {e}')
except Exception as e:
    print(f'予期しないエラー: {e}')
```

### レート制限の処理

```python
import asyncio
from twikit import Client
from twikit.errors import TooManyRequests

async def safe_request(client, func, *args, **kwargs):
    """
    レート制限を考慮した安全なリクエスト実行
    """
    max_retries = 3
    retry_delay = 60  # 秒
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except TooManyRequests:
            if attempt < max_retries - 1:
                print(f'レート制限に達しました。{retry_delay}秒待機します...')
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数バックオフ
            else:
                raise
    
# 使用例
client = Client()
await client.activate()

tweet = await safe_request(
    client, 
    client.get_tweet_by_id, 
    '1234567890123456789'
)
```

## 実用的な使用例

### ツイート監視Bot

```python
import asyncio
from twikit import Client

class TwitterMonitor:
    def __init__(self, target_user):
        self.client = Client()
        self.target_user = target_user
        self.last_tweet_id = None
    
    async def initialize(self):
        await self.client.activate()
        user = await self.client.get_user_by_screen_name(self.target_user)
        tweets = await self.client.get_user_tweets(user.id, 'Tweets', count=1)
        if tweets:
            self.last_tweet_id = tweets[0].id
    
    async def check_new_tweets(self):
        user = await self.client.get_user_by_screen_name(self.target_user)
        tweets = await self.client.get_user_tweets(user.id, 'Tweets', count=5)
        
        new_tweets = []
        for tweet in tweets:
            if self.last_tweet_id and tweet.id > self.last_tweet_id:
                new_tweets.append(tweet)
            elif not self.last_tweet_id:
                new_tweets.append(tweet)
                break
        
        if new_tweets:
            self.last_tweet_id = new_tweets[0].id
            return new_tweets[::-1]  # 古い順に並び替え
        
        return []
    
    async def monitor(self, callback, interval=60):
        await self.initialize()
        
        while True:
            try:
                new_tweets = await self.check_new_tweets()
                for tweet in new_tweets:
                    await callback(tweet)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f'監視エラー: {e}')
                await asyncio.sleep(interval)

# 使用例
async def on_new_tweet(tweet):
    print(f'新しいツイート: {tweet.text}')
    print(f'URL: https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}')

monitor = TwitterMonitor('target_username')
await monitor.monitor(on_new_tweet, interval=30)
```

### 自動返信Bot

```python
from twikit import Client
import asyncio
import re

class AutoReplyBot:
    def __init__(self, keywords, reply_template):
        self.client = Client()
        self.keywords = keywords
        self.reply_template = reply_template
        self.processed_tweets = set()
    
    async def initialize(self, cookies_file):
        self.client.load_cookies(cookies_file)
    
    async def search_and_reply(self):
        for keyword in self.keywords:
            try:
                search_results = await self.client.search_tweet(
                    keyword, 
                    product='Latest'
                )
                
                for tweet in search_results[:5]:  # 最新5件のみ処理
                    if tweet.id not in self.processed_tweets:
                        await self.process_tweet(tweet, keyword)
                        self.processed_tweets.add(tweet.id)
                        
                        # レート制限を避けるため少し待機
                        await asyncio.sleep(2)
                        
            except Exception as e:
                print(f'検索エラー ({keyword}): {e}')
    
    async def process_tweet(self, tweet, keyword):
        # 自分のツイートには返信しない
        if tweet.user.screen_name == 'your_bot_username':
            return
        
        # 既に返信済みかチェック（簡易版）
        if 'your_bot_username' in tweet.text:
            return
        
        # 返信文を生成
        reply_text = self.reply_template.format(
            username=tweet.user.name,
            keyword=keyword
        )
        
        try:
            await tweet.reply(reply_text)
            print(f'返信しました: @{tweet.user.screen_name}')
        except Exception as e:
            print(f'返信エラー: {e}')

# 使用例
bot = AutoReplyBot(
    keywords=['Python', 'プログラミング'],
    reply_template='@{username} さん、{keyword}について興味深いツイートですね！'
)

await bot.initialize('cookies.json')

# 定期実行
while True:
    await bot.search_and_reply()
    await asyncio.sleep(300)  # 5分間隔
```

## パフォーマンス最適化

### 並列処理

```python
import asyncio
from twikit import Client

async def fetch_multiple_tweets(client, tweet_ids):
    """
    複数のツイートを並列で取得
    """
    tasks = []
    for tweet_id in tweet_ids:
        task = client.get_tweet_by_id(tweet_id)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    tweets = []
    for result in results:
        if isinstance(result, Exception):
            print(f'エラー: {result}')
        else:
            tweets.append(result)
    
    return tweets

# 使用例
client = Client()
await client.activate()

tweet_ids = ['123', '456', '789']
tweets = await fetch_multiple_tweets(client, tweet_ids)
```

### キャッシュ機能

```python
import asyncio
from datetime import datetime, timedelta
from twikit import Client

class CachedTwitterClient:
    def __init__(self):
        self.client = Client()
        self.user_cache = {}
        self.tweet_cache = {}
        self.cache_duration = timedelta(minutes=10)
    
    async def get_user_cached(self, screen_name):
        now = datetime.now()
        
        if screen_name in self.user_cache:
            user, cached_time = self.user_cache[screen_name]
            if now - cached_time < self.cache_duration:
                return user
        
        # キャッシュにないか期限切れの場合は新しく取得
        user = await self.client.get_user_by_screen_name(screen_name)
        self.user_cache[screen_name] = (user, now)
        
        return user
    
    async def get_tweet_cached(self, tweet_id):
        now = datetime.now()
        
        if tweet_id in self.tweet_cache:
            tweet, cached_time = self.tweet_cache[tweet_id]
            if now - cached_time < self.cache_duration:
                return tweet
        
        tweet = await self.client.get_tweet_by_id(tweet_id)
        self.tweet_cache[tweet_id] = (tweet, now)
        
        return tweet
```

## セキュリティ考慮事項

### 1. 認証情報の管理

```python
import os
from twikit import Client

# 環境変数から認証情報を取得
username = os.getenv('TWITTER_USERNAME')
email = os.getenv('TWITTER_EMAIL')
password = os.getenv('TWITTER_PASSWORD')

client = Client()
await client.login(
    auth_info_1=username,
    auth_info_2=email,
    password=password
)
```

### 2. Cookieファイルの保護

```python
import os
import json
from pathlib import Path

def save_cookies_securely(client, filename):
    """
    Cookieを安全に保存（ファイル権限を制限）
    """
    cookies_path = Path(filename)
    
    # Cookieを保存
    client.save_cookies(str(cookies_path))
    
    # ファイル権限を所有者のみ読み書き可能に設定
    os.chmod(cookies_path, 0o600)

def load_cookies_securely(client, filename):
    """
    Cookieを安全に読み込み
    """
    cookies_path = Path(filename)
    
    if not cookies_path.exists():
        raise FileNotFoundError(f'Cookieファイルが見つかりません: {filename}')
    
    # ファイル権限をチェック
    file_mode = cookies_path.stat().st_mode & 0o777
    if file_mode != 0o600:
        print('警告: Cookieファイルの権限が適切ではありません')
    
    client.load_cookies(str(cookies_path))
```

### 3. レート制限の遵守

```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests=100, time_window=timedelta(minutes=15)):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def wait_if_needed(self):
        now = datetime.now()
        
        # 時間窓外の古いリクエストを削除
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # 制限に達している場合は待機
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = (oldest_request + self.time_window - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # 現在のリクエストを記録
        self.requests.append(now)

# 使用例
rate_limiter = RateLimiter()

async def safe_api_call(client, func, *args, **kwargs):
    await rate_limiter.wait_if_needed()
    return await func(*args, **kwargs)
```

## トラブルシューティング

### 1. 認証エラー

```python
from twikit import Client
from twikit.errors import Unauthorized

try:
    client = Client()
    await client.login(username, email, password)
except Unauthorized:
    print('認証に失敗しました。以下を確認してください:')
    print('1. ユーザー名/メールアドレスが正しいか')
    print('2. パスワードが正しいか')
    print('3. 2段階認証が有効になっていないか')
    print('4. アカウントがロックされていないか')
```

### 2. Cookie関連の問題

```python
import json
from pathlib import Path
from twikit import Client

def validate_cookies(cookies_file):
    """
    Cookieファイルの妥当性をチェック
    """
    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        required_cookies = ['auth_token', 'ct0']
        missing_cookies = [cookie for cookie in required_cookies 
                          if cookie not in cookies]
        
        if missing_cookies:
            print(f'必要なCookieが不足しています: {missing_cookies}')
            return False
        
        return True
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Cookieファイルの読み込みエラー: {e}')
        return False

# 使用例
if validate_cookies('cookies.json'):
    client = Client()
    client.load_cookies('cookies.json')
else:
    print('Cookieファイルを再生成してください')
```

### 3. ネットワークエラー

```python
import asyncio
from twikit import Client
from twikit.errors import TwikitException

async def robust_request(client, func, *args, max_retries=3, **kwargs):
    """
    ネットワークエラーに対応した堅牢なリクエスト実行
    """
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except TwikitException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数バックオフ
                print(f'リクエスト失敗 (試行 {attempt + 1}/{max_retries}): {e}')
                print(f'{wait_time}秒後に再試行します...')
                await asyncio.sleep(wait_time)
            else:
                raise
```

## ベストプラクティス

### 1. 適切なエラーハンドリング
すべてのAPI呼び出しに例外処理を実装

### 2. レート制限の遵守
Twitter APIの制限を超えないよう適切な間隔でリクエスト

### 3. Cookie管理
認証情報を安全に保存・管理

### 4. 非同期処理の活用
効率的な並列処理でパフォーマンスを向上

### 5. ログ出力
デバッグとモニタリングのためのログ実装

## 参考リンク

- [GitHub リポジトリ](https://github.com/d60/twikit)
- [Twitter API ドキュメント](https://developer.twitter.com/en/docs)
- [Python asyncio ドキュメント](https://docs.python.org/3/library/asyncio.html)

## 更新履歴

- 2025-07-17: 初版作成

---

この仕様書は、twikitライブラリの包括的なガイドとして作成されました。Twitter APIとの効率的で安全な連携にご活用ください。