# Cogs Directory / Cogsディレクトリ

## Overview / 概要

This directory contains Discord bot command implementations and event handlers. Cogs are Discord.py's way of organizing bot functionality into separate, modular components.

このディレクトリには、Discord botコマンドの実装とイベントハンドラーが含まれています。CogsはDiscord.pyでbot機能を別々のモジュラーコンポーネントに整理する方法です。

## Files / ファイル

### twitter_commands.py
Contains the `TwitterCommandsCog` class that implements Discord slash commands for Twitter feed management.

Twitter フィード管理用の Discord スラッシュコマンドを実装する `TwitterCommandsCog` クラスが含まれています。

**Key Commands / 主要コマンド:**
- `/set` - Add a Twitter user to the feed / Twitter ユーザーをフィードに追加
- `/del` - Remove a Twitter user from the feed / Twitter ユーザーをフィードから削除
- `/cool_down` - Set the check interval for tweets / ツイートのチェック間隔を設定
- `/check_setting` - Display current bot settings / 現在のbot設定を表示
- `/test_tweet` - Test tweet analysis with a specific URL / 特定のURLでツイート分析をテスト
- `/generate_rss` - Generate RSS feed for a Twitter user / Twitter ユーザーのRSSフィードを生成

**Key Features / 主な機能:**
- Automatic tweet fetching loop / 自動ツイート取得ループ
- Tweet embed generation / ツイート埋め込み生成
- Settings management / 設定管理
- RSS feed generation / RSSフィード生成

### url_fixer.py
Contains the `URLFixerCog` class that handles automatic URL conversion for better Discord embeds.

より良いDiscord埋め込みのための自動URL変換を処理する `URLFixerCog` クラスが含まれています。

**Key Features / 主な機能:**
- **Twitter/X URL Enhancement** / **Twitter/X URL拡張**: Converts `twitter.com` and `x.com` URLs to `fxtwitter.com` for better embeds / より良い埋め込みのために `twitter.com` と `x.com` のURLを `fxtwitter.com` に変換
- **TikTok URL Enhancement** / **TikTok URL拡張**: Converts `tiktok.com` URLs to `fxtiktok.com` for better embeds / より良い埋め込みのために `tiktok.com` のURLを `fxtiktok.com` に変換
- **Tweet Analysis Integration** / **ツイート分析統合**: Analyzes tweets and provides additional context / ツイートを分析し、追加のコンテキストを提供
- **Batch Message Processing** / **バッチメッセージ処理**: Efficiently handles multiple URL replacements / 複数のURL置換を効率的に処理

## Architecture / アーキテクチャ

Both cogs follow the Discord.py cog pattern:

両方のcogsはDiscord.py cogパターンに従います：

1. **Initialization** / **初期化**: Set up bot reference and configuration / bot参照と設定をセットアップ
2. **Event Handlers** / **イベントハンドラー**: Handle Discord events (messages, interactions) / Discordイベント（メッセージ、インタラクション）を処理
3. **Command Handlers** / **コマンドハンドラー**: Process slash commands and user interactions / スラッシュコマンドとユーザーインタラクションを処理
4. **Background Tasks** / **バックグラウンドタスク**: Run periodic tasks (tweet fetching) / 定期的なタスク（ツイート取得）を実行

## Dependencies / 依存関係

- `discord.py` - Discord bot framework / Discord botフレームワーク
- `src.core.twitter_analyzer` - Tweet analysis functionality / ツイート分析機能
- `src.rss.rss_generator` - RSS generation utilities / RSS生成ユーティリティ
- `src.config.settings` - Configuration management / 設定管理

## Usage / 使用方法

These cogs are automatically loaded by the main bot instance. Users interact with them through Discord slash commands and message events.

これらのcogsはメインのbotインスタンスによって自動的にロードされます。ユーザーはDiscordスラッシュコマンドとメッセージイベントを通じてそれらと対話します。

For detailed command usage, use the `/check_setting` command in Discord to see available options and current configuration.

詳細なコマンドの使用方法については、Discordで `/check_setting` コマンドを使用して、利用可能なオプションと現在の設定を確認してください。