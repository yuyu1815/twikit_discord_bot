# Config Directory / Configディレクトリ

## Overview / 概要

This directory contains configuration management and settings persistence functionality for the Twikit Discord Bot. It handles database operations, language file loading, and guild-specific configurations.

このディレクトリには、Twikit Discord Botの設定管理と設定永続化機能が含まれています。データベース操作、言語ファイルの読み込み、ギルド固有の設定を処理します。

## Files / ファイル

### settings.py
Contains the `Settings` class that manages all configuration and file I/O operations for the bot.

botのすべての設定とファイルI/O操作を管理する `Settings` クラスが含まれています。

## Key Features / 主な機能

### Language Management / 言語管理
- **Multi-language Support** / **多言語サポート**: Loads and manages language files (English, Japanese, Chinese) / 言語ファイル（英語、日本語、中国語）の読み込みと管理
- **Dynamic Language Loading** / **動的言語読み込み**: Supports runtime language switching / ランタイム言語切り替えをサポート

### Guild Configuration / ギルド設定
- **Per-Guild Settings** / **ギルド別設定**: Manages individual settings for each Discord server / 各Discordサーバーの個別設定を管理
- **Channel Management** / **チャンネル管理**: Tracks which channels are configured for tweet feeds / ツイートフィード用に設定されたチャンネルを追跡
- **User Management** / **ユーザー管理**: Manages Twitter usernames to follow per guild / ギルドごとにフォローするTwitterユーザー名を管理
- **Cooldown Settings** / **クールダウン設定**: Configures tweet check intervals / ツイートチェック間隔を設定

### Database Operations / データベース操作
- **Twitter Message Tracking** / **Twitterメッセージ追跡**: Stores and retrieves Twitter message data / Twitterメッセージデータの保存と取得
- **Configuration Persistence** / **設定永続化**: Saves guild configurations to database / ギルド設定をデータベースに保存
- **Data Cleanup** / **データクリーンアップ**: Manages deletion of outdated configurations / 古い設定の削除を管理

## Class Methods / クラスメソッド

### Settings Class / Settingsクラス

#### Language Methods / 言語メソッド
- `get_lang_json(lang)` - Load language file for specified locale / 指定されたロケールの言語ファイルを読み込み

#### Configuration Methods / 設定メソッド
- `get_guild_config(guild_id)` - Retrieve configuration for a specific guild / 特定のギルドの設定を取得
- `update_guild_config(guild_id, ...)` - Update guild configuration settings / ギルド設定を更新
- `get_all_guild_ids()` - Get list of all configured guild IDs / 設定されたすべてのギルドIDのリストを取得

#### Twitter Message Methods / Twitterメッセージメソッド
- `get_twitter_msg(channel_id, twitter_id)` - Retrieve Twitter message data / Twitterメッセージデータを取得
- `update_twitter_msg(channel_id, twitter_id, msg)` - Update Twitter message data / Twitterメッセージデータを更新
- `delete_twitter_msg(channel_id, twitter_id)` - Delete Twitter message data / Twitterメッセージデータを削除

#### Utility Methods / ユーティリティメソッド
- `twitter_new_json_edit()` - Initialize or update Twitter configuration / Twitter設定の初期化または更新

## Configuration Structure / 設定構造

The Settings class manages the following configuration parameters:

Settingsクラスは以下の設定パラメータを管理します：

```python
{
    "cool_down_time": int,          # Tweet check interval in minutes / ツイートチェック間隔（分）
    "setting_channels": [int],      # List of configured channel IDs / 設定されたチャンネルIDのリスト
    "twitter_user_names": [str],    # List of Twitter usernames to follow / フォローするTwitterユーザー名のリスト
    "setting_bool": bool,           # Enable/disable tweet fetching / ツイート取得の有効/無効
    "last_checked_time": str        # Last tweet check timestamp / 最後のツイートチェックタイムスタンプ
}
```

## Dependencies / 依存関係

- `json` - JSON file processing / JSONファイル処理
- `os` - Operating system interface / オペレーティングシステムインターフェース
- `pathlib.Path` - File path operations / ファイルパス操作
- `src.core.database` - Database operations (implicit) / データベース操作（暗黙的）

## Usage / 使用方法

The Settings class is typically instantiated with a language parameter and used throughout the bot for configuration management:

Settingsクラスは通常、言語パラメータでインスタンス化され、設定管理のためにbot全体で使用されます：

```python
from src.config.settings import Settings

# Initialize with default language
settings = Settings(language='ja_JP')

# Get guild configuration
config = settings.get_guild_config(guild_id)

# Update configuration
settings.update_guild_config(
    guild_id=guild_id,
    cool_down_time=30,
    twitter_user_names=['username1', 'username2']
)
```

## File Locations / ファイルの場所

- **Language Files** / **言語ファイル**: `src/lang/` directory / `src/lang/` ディレクトリ
- **Database** / **データベース**: `data/bot.db` (SQLite database) / `data/bot.db`（SQLiteデータベース）
- **Configuration Cache** / **設定キャッシュ**: In-memory storage with database persistence / データベース永続化を伴うメモリ内ストレージ