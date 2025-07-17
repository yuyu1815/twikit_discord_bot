# Source Directory / ソースディレクトリ

## Overview / 概要

This directory contains the main source code for the Twikit Discord Bot. The project follows a modular architecture with clear separation of concerns.

このディレクトリには、Twikit Discord Botのメインソースコードが含まれています。プロジェクトは明確な関心の分離を持つモジュラーアーキテクチャに従っています。

## Directory Structure / ディレクトリ構造

```
src/
├── cogs/           # Discord bot commands and event handlers / Discord botコマンドとイベントハンドラー
├── config/         # Configuration management / 設定管理
├── core/           # Core functionality and business logic / コア機能とビジネスロジック
├── lang/           # Multi-language support files / 多言語サポートファイル
└── rss/            # RSS generation functionality / RSS生成機能
```

## Key Features / 主な機能

- **Automatic Tweet Acquisition** / **自動ツイート取得**: Fetches tweets without cost using Twitter cookies / Twitterクッキーを使用してコストなしでツイートを取得
- **Multi-server Support** / **マルチサーバーサポート**: Works across multiple Discord servers and channels / 複数のDiscordサーバーとチャンネルで動作
- **URL Enhancement** / **URL拡張**: Automatically converts Twitter/X and TikTok URLs to fxtwitter and fxtiktok / Twitter/XとTikTokのURLを自動的にfxtwitterとfxtiktokに変換
- **Multi-language Support** / **多言語サポート**: Available in English, Japanese, and Chinese / 英語、日本語、中国語で利用可能
- **RSS-like Functionality** / **RSS風機能**: Fetches the latest tweets from users similar to an RSS feed / RSSフィードのようにユーザーから最新のツイートを取得

## Architecture / アーキテクチャ

The project is organized into the following modules:

プロジェクトは以下のモジュールに整理されています：

- **cogs/**: Discord bot command implementations / Discord botコマンドの実装
- **config/**: Configuration and settings management / 設定と設定管理
- **core/**: Core business logic and Twitter integration / コアビジネスロジックとTwitter統合
- **lang/**: Internationalization and localization files / 国際化とローカライゼーションファイル
- **rss/**: RSS feed generation utilities / RSSフィード生成ユーティリティ

## Getting Started / はじめに

Each subdirectory contains its own README.md file with detailed information about its specific functionality and usage.

各サブディレクトリには、その特定の機能と使用方法に関する詳細情報を含む独自のREADME.mdファイルが含まれています。

For setup instructions, refer to the main README.md file in the project root.

セットアップ手順については、プロジェクトルートのメインREADME.mdファイルを参照してください。