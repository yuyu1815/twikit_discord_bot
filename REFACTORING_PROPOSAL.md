# プロジェクトリファクタリング提案書 (改訂版)

このドキュメントは、`twikit_discord_bot` プロジェクトのソースコードを分析した上で、保守性、可読性、拡張性を向上させるための具体的なリファクタリング案をまとめたものです。

## 1. 分析結果

- **`Bot.py`の肥大化**: イベントハンドラ、多数のコマンド、バックグラウンドタスクが1ファイルに混在し、見通しが悪い。グローバル変数の多用も状態管理を複雑にしている。
- **`json_make.py`の責務過多**: 設定、言語ファイル、Twitterデータなど、関連性の低い複数のファイルI/O処理が混在している。パスがハードコーディングされており、構成変更に弱い。
- **`twitter_get.py`の改善点**: `TwitterClient`クラスは良い設計だが、同期的なHTTPリクエスト (`requests`) が非同期処理をブロックする可能性がある。エラーハンドリングもより具体的にできる。
- **`scraping/aliexpress.py`の現状**: `Bot.py`内で関連コードがコメントアウトされており、現在使用されているか不明。

---

## 2. 推奨される新しいフォルダ構成

分析に基づき、責務が明確になるようにフォルダとファイルを再配置します。

```
twikit_discord_bot/
├── .venv/
├── data/                     # アプリケーションが使用・生成するデータ
│   ├── cookie.json
│   ├── cookie_edit.json
│   ├── DiscordSetting.json
│   └── Twitter_msg.json
├── src/
│   ├── __init__.py
│   ├── cogs/                   # Discordコマンドやイベントリスナーを機能単位で格納
│   │   ├── __init__.py
│   │   ├── twitter_commands.py # Twitter関連のスラッシュコマンド
│   │   └── url_fixer.py        # URL置換を行うイベントリスナー
│   ├── core/                   # ボットの中核機能
│   │   ├── __init__.py
│   │   ├── bot.py              # Bot本体の定義、初期化、タスクループ
│   │   └── twitter_client.py   # Twitter API連携クライアント
│   ├── config/                 # 設定関連
│   │   ├── __init__.py
│   │   └── settings.py         # 設定/言語/データファイルの読み込み・管理クラス
│   └── lang/                   # 言語ファイル
│       ├── en_US.json
│       ├── ja_JP.json
│       └── zh_CN.json
├── .env
├── .gitignore
├── main.py                     # アプリケーションの起動スクリプト
├── requirements.txt
└── README.md
```

---

## 3. 主要ファイルの役割とリファクタリング方針

### `main.py` (新規作成)
- **役割**: アプリケーションの唯一のエントリーポイント。
- **実装**:
  1. `dotenv.load_dotenv()` を実行。
  2. `src.core.bot` からBotインスタンスを起動する関数を呼び出す。

### `src/core/bot.py` (新規作成)
- **役割**: Discordボットの本体。`discord.ext.commands.Bot`を継承し、各種クライアントや設定をインスタンス内で管理する。
- **リファクタリング内容**:
  - `Bot.py`からDiscordクライアントの初期化、`on_ready`イベント、`@tasks.loop`を移設。
  - カスタムBotクラス (`MyBot`) を作成し、`twitter_client` や `settings` オブジェクトをインスタンス変数として保持することで、グローバル変数を排除する。
  - `setup_hook` メソッド内で `src/cogs/` ディレクトリ内のCogを動的に読み込む。

### `src/config/settings.py` (旧 `json_make.py` を刷新)
- **役割**: すべてのファイルI/O（設定、言語、データ）を責務とする設定管理クラス。
- **実装**:
  - `Settings` クラスとして実装。
  - プロジェクトルートからの相対パスで、各種JSONファイルへのパスを管理する。
  - `get_guild_config(guild_id)`, `update_guild_config(...)` のように、目的別のメソッドを提供する。
  - `json_make.py` 内の各関数を、このクラスのメソッドとして再整理する。

### `src/core/twitter_client.py` (旧 `twitter_get.py` を改善)
- **役割**: Twitter APIとの通信を完全にカプセル化する。
- **リファクタリング内容**:
  - `__init__` で認証情報（クッキー）を受け取るように変更。
  - 同期的な `requests.get` を非同期HTTPクライアント `aiohttp` を使ったリクエストに置き換える。
  - `twikit` が投げる可能性のある具体的な例外（例: `UserNotFound`）を捕捉し、より丁寧なエラーハンドリングを行う。

### `src/cogs/twitter_commands.py` (新規作成)
- **役割**: `/set_twitter`, `/del_twitter`, `/check-time` など、ユーザーが直接実行するスラッシュコマンド群を管理する。
- **実装**:
  - `discord.ext.commands.Cog` を継承した `TwitterCommandsCog` クラスを作成。
  - `__init__` でBotインスタンスを受け取り、`bot.settings` や `bot.twitter_client` を通じて他の機能と連携する。
  - `Bot.py` にあったコマンドのロジックを、Cog内のメソッドとして移植する。

### `src/cogs/url_fixer.py` (新規作成)
- **役割**: `on_message` イベントを監視し、投稿されたメッセージ内のURLを置換する機能。
- **実装**:
  - `discord.ext.commands.Cog` を継承した `URLFixerCog` クラスを作成。
  - `@commands.Cog.listener()` デコレータを使って `on_message` イベントを処理する。
  - `Bot.py` の `on_message` ハンドラのロジックを移植する。

---

## 4. データと設定ファイルの移行

- **データファイル**: `src/twitter_json/` 内の `DiscordSetting.json`, `Twitter_msg.json`, `cookie.json`, `cookie_edit.json` は、新設する `data/` ディレクトリに移動する。
- **言語ファイル**: `src/lang/` はそのままの位置で問題ない。
- **`.env`ファイル**: `TOKEN`などの重要な認証情報は、プロジェクトのルートディレクトリにある`.env`ファイルで管理することを徹底する。

この計画に沿ってリファクタリングを進めることで、コードの各部分が何をすべきか明確になり、将来の機能追加やバグ修正が格段に容易になります。