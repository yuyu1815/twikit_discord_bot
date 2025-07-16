# twikit 関数一覧

## 概要

このドキュメントは、twikitライブラリの主要な関数とメソッドの包括的な一覧です。Twitter API v2を使用してTwitterとやり取りするための非公式ライブラリの全機能を網羅しています。

## 基本情報
- **ライブラリ名**: twikit
- **対応API**: Twitter API v2
- **公式リポジトリ**: https://github.com/d60/twikit
- **ライセンス**: MIT License

## 主要クラス

### Client クラス
Twitter APIとの基本的な接続を管理するメインクラス

#### 初期化・認証関連
- `Client(language='en-US')` - クライアントを初期化
- `activate()` - ゲストとしてアクティベート
- `login(auth_info_1, auth_info_2, password)` - ユーザー名/パスワードでログイン
- `load_cookies(path)` - Cookieファイルから認証情報を読み込み
- `save_cookies(path)` - 認証情報をCookieファイルに保存

#### ツイート関連メソッド
- `get_tweet_by_id(tweet_id)` - ツイートIDからツイートを取得
- `get_user_tweets(user_id, tweet_type='Tweets', count=20)` - ユーザーのツイートを取得
- `create_tweet(text, *, media_ids=None, reply_to=None)` - ツイートを投稿
- `delete_tweet(tweet_id)` - ツイートを削除
- `retweet(tweet_id)` - ツイートをリツイート
- `unretweet(tweet_id)` - リツイートを取り消し
- `favorite_tweet(tweet_id)` - ツイートにいいね
- `unfavorite_tweet(tweet_id)` - いいねを取り消し

#### ユーザー関連メソッド
- `get_user_by_screen_name(screen_name)` - スクリーン名からユーザーを取得
- `get_user_by_id(user_id)` - ユーザーIDからユーザーを取得
- `follow_user(user_id)` - ユーザーをフォロー
- `unfollow_user(user_id)` - ユーザーをアンフォロー
- `get_user_followers(user_id, count=20)` - ユーザーのフォロワーを取得
- `get_user_following(user_id, count=20)` - ユーザーのフォロー中を取得

#### 検索関連メソッド
- `search_tweet(query, product='Latest', count=20)` - ツイートを検索
- `search_user(query, count=20)` - ユーザーを検索
- `get_trends(woeid=1)` - トレンドを取得

#### リスト関連メソッド
- `get_list(list_id)` - リストを取得
- `get_list_tweets(list_id, count=20)` - リストのツイートを取得
- `create_list(name, description=None, private=False)` - リストを作成
- `delete_list(list_id)` - リストを削除
- `add_list_member(list_id, user_id)` - リストにメンバーを追加
- `remove_list_member(list_id, user_id)` - リストからメンバーを削除

#### メディア関連メソッド
- `upload_media(media_path, media_type=None)` - メディアをアップロード
- `create_media_metadata(media_id, alt_text)` - メディアメタデータを作成

### GuestClient クラス
認証不要のゲストクライアント

#### 基本メソッド
- `GuestClient()` - ゲストクライアントを初期化
- `activate()` - ゲストクライアントをアクティベート
- `get_tweet_by_id(tweet_id)` - ツイートを取得（認証不要）
- `get_user_by_screen_name(screen_name)` - ユーザーを取得（認証不要）
- `search_tweet(query, product='Latest')` - ツイート検索（認証不要）

### Tweet クラス
ツイートデータを表現するクラス

#### 基本属性
- `id` - ツイートID
- `text` - ツイート内容
- `full_text` - 完全なツイート内容
- `user` - 投稿者のUserオブジェクト
- `created_at` - 投稿日時
- `favorite_count` - いいね数
- `retweet_count` - リツイート数
- `reply_count` - 返信数
- `quote_count` - 引用数
- `view_count` - 表示数

#### 状態属性
- `is_quote_status` - 引用ツイートかどうか
- `retweeted_tweet` - リツイート元のツイート
- `quoted_tweet` - 引用元のツイート
- `in_reply_to` - 返信先のツイートID
- `lang` - ツイートの言語

#### メディア関連属性
- `media` - 添付メディアのリスト
- `urls` - 含まれるURLのリスト
- `hashtags` - ハッシュタグのリスト
- `mentions` - メンションのリスト

#### ツイート操作メソッド
- `reply(text, *, media_ids=None)` - このツイートに返信
- `retweet()` - このツイートをリツイート
- `unretweet()` - リツイートを取り消し
- `favorite()` - このツイートにいいね
- `unfavorite()` - いいねを取り消し
- `delete()` - このツイートを削除

### User クラス
ユーザーデータを表現するクラス

#### 基本属性
- `id` - ユーザーID
- `name` - 表示名
- `screen_name` - スクリーン名（@以降）
- `description` - プロフィール
- `location` - 場所
- `url` - プロフィールURL
- `created_at` - アカウント作成日時

#### 統計属性
- `followers_count` - フォロワー数
- `friends_count` - フォロー数
- `statuses_count` - ツイート数
- `favourites_count` - いいね数
- `listed_count` - リスト登録数

#### 状態属性
- `verified` - 認証済みかどうか
- `protected` - 非公開アカウントかどうか
- `default_profile` - デフォルトプロフィールかどうか
- `default_profile_image` - デフォルトプロフィール画像かどうか

#### プロフィール画像・バナー
- `profile_image_url` - プロフィール画像URL
- `profile_image_url_https` - プロフィール画像URL（HTTPS）
- `profile_banner_url` - プロフィールバナーURL

#### ユーザー操作メソッド
- `follow()` - このユーザーをフォロー
- `unfollow()` - このユーザーをアンフォロー
- `get_tweets(tweet_type='Tweets', count=20)` - このユーザーのツイートを取得
- `send_dm(text)` - このユーザーにDMを送信

### List クラス
Twitterリストを表現するクラス

#### 基本属性
- `id` - リストID
- `name` - リスト名
- `description` - リストの説明
- `mode` - リストのモード（public/private）
- `member_count` - メンバー数
- `subscriber_count` - 購読者数
- `created_at` - 作成日時
- `owner` - リストオーナー

#### リスト操作メソッド
- `get_tweets(count=20)` - リストのツイートを取得
- `get_members(count=20)` - リストのメンバーを取得
- `add_member(user_id)` - メンバーを追加
- `remove_member(user_id)` - メンバーを削除
- `subscribe()` - リストを購読
- `unsubscribe()` - 購読を解除
- `delete()` - リストを削除

### Media クラス
メディアファイルを表現するクラス

#### 基本属性
- `id` - メディアID
- `media_url` - メディアURL
- `media_url_https` - メディアURL（HTTPS）
- `type` - メディアタイプ（photo/video/animated_gif）
- `sizes` - 利用可能なサイズ

#### 動画関連属性
- `video_info` - 動画情報
- `duration_millis` - 動画の長さ（ミリ秒）
- `variants` - 動画の品質バリエーション

#### メディア操作メソッド
- `download(path=None)` - メディアをダウンロード
- `get_best_quality()` - 最高品質のバリエーションを取得

## ユーティリティ関数

### 認証関連
- `get_guest_token()` - ゲストトークンを取得
- `refresh_token()` - トークンをリフレッシュ
- `validate_session()` - セッションの有効性を確認

### データ変換
- `parse_tweet_data(raw_data)` - 生データからTweetオブジェクトを作成
- `parse_user_data(raw_data)` - 生データからUserオブジェクトを作成
- `format_datetime(timestamp)` - タイムスタンプを日時に変換

### URL処理
- `expand_url(short_url)` - 短縮URLを展開
- `extract_urls(text)` - テキストからURLを抽出
- `extract_hashtags(text)` - テキストからハッシュタグを抽出
- `extract_mentions(text)` - テキストからメンションを抽出

## エラークラス

### 基本例外
- `TwikitException` - 基本例外クラス
- `BadRequest` - 不正なリクエスト（400）
- `Unauthorized` - 認証エラー（401）
- `Forbidden` - アクセス禁止（403）
- `NotFound` - リソース未発見（404）
- `TooManyRequests` - レート制限（429）
- `ServerError` - サーバーエラー（5xx）

### 認証関連例外
- `LoginRequired` - ログインが必要
- `InvalidCredentials` - 認証情報が無効
- `AccountLocked` - アカウントがロック
- `AccountSuspended` - アカウントが凍結

### データ関連例外
- `TweetNotFound` - ツイートが見つからない
- `UserNotFound` - ユーザーが見つからない
- `InvalidTweetId` - 無効なツイートID
- `InvalidUserId` - 無効なユーザーID

## 定数・列挙型

### ツイートタイプ
- `TWEET_TYPE_TWEETS` - 通常のツイート
- `TWEET_TYPE_REPLIES` - 返信
- `TWEET_TYPE_MEDIA` - メディア付きツイート
- `TWEET_TYPE_LIKES` - いいねしたツイート

### 検索製品タイプ
- `SEARCH_PRODUCT_LATEST` - 最新
- `SEARCH_PRODUCT_POPULAR` - 人気
- `SEARCH_PRODUCT_PHOTOS` - 写真
- `SEARCH_PRODUCT_VIDEOS` - 動画

### メディアタイプ
- `MEDIA_TYPE_PHOTO` - 写真
- `MEDIA_TYPE_VIDEO` - 動画
- `MEDIA_TYPE_ANIMATED_GIF` - アニメーションGIF

## 設定・構成

### クライアント設定
- `set_language(language)` - 言語を設定
- `set_timeout(timeout)` - タイムアウトを設定
- `set_retry_count(count)` - リトライ回数を設定
- `set_user_agent(user_agent)` - ユーザーエージェントを設定

### プロキシ設定
- `set_proxy(proxy_url)` - プロキシを設定
- `remove_proxy()` - プロキシ設定を削除

### ログ設定
- `enable_logging(level='INFO')` - ログを有効化
- `disable_logging()` - ログを無効化
- `set_log_file(path)` - ログファイルを設定

## 実用的なヘルパー関数

### バッチ処理
- `batch_get_tweets(tweet_ids)` - 複数ツイートを一括取得
- `batch_get_users(user_ids)` - 複数ユーザーを一括取得
- `batch_follow_users(user_ids)` - 複数ユーザーを一括フォロー
- `batch_unfollow_users(user_ids)` - 複数ユーザーを一括アンフォロー

### フィルタリング
- `filter_tweets_by_date(tweets, start_date, end_date)` - 日付でツイートをフィルタ
- `filter_tweets_by_user(tweets, user_ids)` - ユーザーでツイートをフィルタ
- `filter_tweets_by_hashtag(tweets, hashtags)` - ハッシュタグでツイートをフィルタ
- `filter_tweets_by_media(tweets, media_type)` - メディアタイプでツイートをフィルタ

### 統計・分析
- `calculate_engagement_rate(tweet)` - エンゲージメント率を計算
- `get_tweet_metrics(tweet)` - ツイートの指標を取得
- `analyze_user_activity(user)` - ユーザーの活動を分析
- `get_hashtag_frequency(tweets)` - ハッシュタグの頻度を取得

### データエクスポート
- `export_tweets_to_csv(tweets, filename)` - ツイートをCSVにエクスポート
- `export_users_to_json(users, filename)` - ユーザーをJSONにエクスポート
- `export_media_urls(tweets, filename)` - メディアURLをエクスポート

## 非同期サポート

### 非同期メソッド
- `async_get_tweet_by_id(tweet_id)` - 非同期ツイート取得
- `async_get_user_by_screen_name(screen_name)` - 非同期ユーザー取得
- `async_search_tweet(query, product='Latest')` - 非同期ツイート検索
- `async_create_tweet(text)` - 非同期ツイート投稿

### 並列処理サポート
- `parallel_get_tweets(tweet_ids, max_workers=5)` - 並列ツイート取得
- `parallel_get_users(user_ids, max_workers=5)` - 並列ユーザー取得
- `parallel_process_tweets(tweets, processor_func)` - 並列ツイート処理

## レート制限管理

### レート制限情報
- `get_rate_limit_status()` - レート制限状況を取得
- `get_remaining_requests(endpoint)` - 残りリクエスト数を取得
- `get_reset_time(endpoint)` - リセット時刻を取得

### レート制限処理
- `wait_for_rate_limit_reset(endpoint)` - レート制限リセットまで待機
- `handle_rate_limit_error(error)` - レート制限エラーを処理
- `auto_retry_on_rate_limit(func, *args, **kwargs)` - レート制限時自動リトライ

## キャッシュ機能

### キャッシュ管理
- `enable_cache(cache_size=1000)` - キャッシュを有効化
- `disable_cache()` - キャッシュを無効化
- `clear_cache()` - キャッシュをクリア
- `get_cache_stats()` - キャッシュ統計を取得

### キャッシュ操作
- `cache_tweet(tweet)` - ツイートをキャッシュ
- `get_cached_tweet(tweet_id)` - キャッシュからツイートを取得
- `cache_user(user)` - ユーザーをキャッシュ
- `get_cached_user(user_id)` - キャッシュからユーザーを取得

## デバッグ・監視

### デバッグ機能
- `enable_debug_mode()` - デバッグモードを有効化
- `disable_debug_mode()` - デバッグモードを無効化
- `log_request(method, url, params)` - リクエストをログ出力
- `log_response(response)` - レスポンスをログ出力

### 監視機能
- `get_request_count()` - リクエスト数を取得
- `get_error_count()` - エラー数を取得
- `get_success_rate()` - 成功率を取得
- `reset_statistics()` - 統計をリセット

## 設定ファイル管理

### 設定読み込み
- `load_config(config_path)` - 設定ファイルを読み込み
- `save_config(config_path)` - 設定ファイルを保存
- `get_default_config()` - デフォルト設定を取得
- `validate_config(config)` - 設定を検証

### 環境変数サポート
- `load_from_env()` - 環境変数から設定を読み込み
- `get_env_var(key, default=None)` - 環境変数を取得
- `set_env_var(key, value)` - 環境変数を設定

## 更新履歴

- 2025-07-17: 初版作成
  - 主要クラス（Client、Tweet、User、List、Media）の包括的な関数一覧を作成
  - エラークラス、ユーティリティ関数、設定管理機能を網羅
  - 実用的なヘルパー関数と非同期サポート機能を追加
  - レート制限管理、キャッシュ機能、デバッグ・監視機能を含む

---

この関数一覧は、twikitライブラリを使用したTwitter API連携開発において、必要な関数やメソッドを素早く見つけるためのリファレンスとして活用してください。