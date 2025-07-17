# Lang Directory / Langディレクトリ

## Overview / 概要

This directory contains language files for multi-language support in the Twikit Discord Bot. The bot supports English, Japanese, and Chinese languages through JSON-based localization files.

このディレクトリには、Twikit Discord Botの多言語サポート用の言語ファイルが含まれています。botはJSONベースのローカライゼーションファイルを通じて英語、日本語、中国語をサポートしています。

## Files / ファイル

### en_US.json
English language file containing all user-facing text and messages.

すべてのユーザー向けテキストとメッセージを含む英語言語ファイル。

### ja_JP.json
Japanese language file containing all user-facing text and messages.

すべてのユーザー向けテキストとメッセージを含む日本語言語ファイル。

### zh_CN.json
Chinese (Simplified) language file containing all user-facing text and messages.

すべてのユーザー向けテキストとメッセージを含む中国語（簡体字）言語ファイル。

## Language Structure / 言語構造

Each language file follows the same JSON structure with nested categories for different types of messages:

各言語ファイルは、異なるタイプのメッセージのネストされたカテゴリを持つ同じJSON構造に従います：

```json
{
    "commands": {
        "set": {
            "description": "Add a Twitter user to the feed",
            "success": "Successfully added {user} to the feed",
            "error": "Failed to add user to the feed"
        },
        "del": {
            "description": "Remove a Twitter user from the feed",
            "success": "Successfully removed {user} from the feed",
            "error": "User not found in the feed"
        }
    },
    "errors": {
        "twitter_api": "Twitter API error occurred",
        "network": "Network connection error",
        "database": "Database operation failed"
    },
    "messages": {
        "tweet_posted": "New tweet from {user}",
        "thread_detected": "Thread detected with {count} tweets",
        "analysis_complete": "Tweet analysis completed"
    }
}
```

## Key Categories / 主要カテゴリ

### Commands / コマンド
Contains text for Discord slash commands including:

以下を含むDiscordスラッシュコマンドのテキストが含まれています：

- **Command Descriptions** / **コマンド説明**: Help text for each command / 各コマンドのヘルプテキスト
- **Success Messages** / **成功メッセージ**: Confirmation messages for successful operations / 成功した操作の確認メッセージ
- **Error Messages** / **エラーメッセージ**: Error notifications for failed operations / 失敗した操作のエラー通知

### Errors / エラー
Error messages for various failure scenarios:

さまざまな失敗シナリオのエラーメッセージ：

- **Twitter API Errors** / **Twitter APIエラー**: Rate limits, authentication failures / レート制限、認証失敗
- **Network Errors** / **ネットワークエラー**: Connection issues / 接続問題
- **Database Errors** / **データベースエラー**: Data storage problems / データストレージ問題
- **Validation Errors** / **検証エラー**: Input validation failures / 入力検証失敗

### Messages / メッセージ
General bot messages and notifications:

一般的なbotメッセージと通知：

- **Tweet Notifications** / **ツイート通知**: New tweet announcements / 新しいツイートのお知らせ
- **Status Updates** / **ステータス更新**: Bot status and operation messages / botステータスと操作メッセージ
- **Analysis Results** / **分析結果**: Tweet analysis feedback / ツイート分析フィードバック

## Localization Features / ローカライゼーション機能

### Parameter Substitution / パラメータ置換
Language files support parameter substitution using curly braces:

言語ファイルは中括弧を使用したパラメータ置換をサポートします：

```json
{
    "welcome": "Welcome {username} to {server_name}!",
    "tweet_count": "Found {count} new tweets from {user}"
}
```

### Pluralization Support / 複数形サポート
Some languages include pluralization rules for count-dependent messages:

一部の言語には、カウント依存メッセージの複数形ルールが含まれています：

```json
{
    "tweet_singular": "1 new tweet",
    "tweet_plural": "{count} new tweets"
}
```

### Cultural Adaptations / 文化的適応
Language files include culturally appropriate expressions and formatting:

言語ファイルには文化的に適切な表現とフォーマットが含まれています：

- **Date/Time Formats** / **日付/時刻フォーマット**: Localized date and time representations / ローカライズされた日付と時刻の表現
- **Politeness Levels** / **丁寧さレベル**: Appropriate formality for each culture / 各文化に適した形式性
- **Cultural References** / **文化的参照**: Region-specific terminology and concepts / 地域固有の用語と概念

## Usage / 使用方法

Language files are loaded by the `Settings` class in `src/config/settings.py`:

言語ファイルは `src/config/settings.py` の `Settings` クラスによって読み込まれます：

```python
from src.config.settings import Settings

# Initialize with specific language
settings = Settings(language='ja_JP')

# Get localized text
welcome_message = settings.get_lang_json('ja_JP')['messages']['welcome']
```

### Dynamic Language Switching / 動的言語切り替え
The bot supports runtime language switching based on:

botは以下に基づくランタイム言語切り替えをサポートします：

- **Guild Settings** / **ギルド設定**: Per-server language preferences / サーバーごとの言語設定
- **User Preferences** / **ユーザー設定**: Individual user language choices / 個別ユーザーの言語選択
- **Auto-detection** / **自動検出**: Discord client language detection / Discordクライアント言語検出

## Adding New Languages / 新しい言語の追加

To add support for a new language:

新しい言語のサポートを追加するには：

1. **Create Language File** / **言語ファイルを作成**: Copy an existing file (e.g., `en_US.json`) / 既存のファイル（例：`en_US.json`）をコピー
2. **Translate Content** / **コンテンツを翻訳**: Translate all text while maintaining JSON structure / JSON構造を維持しながらすべてのテキストを翻訳
3. **Update Settings** / **設定を更新**: Add the new language code to the Settings class / 新しい言語コードをSettingsクラスに追加
4. **Test Functionality** / **機能をテスト**: Verify all messages display correctly / すべてのメッセージが正しく表示されることを確認

### Language File Naming / 言語ファイル命名
Follow the ISO 639-1 and ISO 3166-1 standards:

ISO 639-1およびISO 3166-1標準に従います：

- `en_US.json` - English (United States) / 英語（アメリカ）
- `ja_JP.json` - Japanese (Japan) / 日本語（日本）
- `zh_CN.json` - Chinese Simplified (China) / 中国語簡体字（中国）
- `fr_FR.json` - French (France) / フランス語（フランス）
- `de_DE.json` - German (Germany) / ドイツ語（ドイツ）

## Maintenance / メンテナンス

### Consistency Checks / 一貫性チェック
Regular maintenance should include:

定期的なメンテナンスには以下が含まれるべきです：

- **Key Validation** / **キー検証**: Ensure all language files have the same keys / すべての言語ファイルが同じキーを持つことを確認
- **Parameter Matching** / **パラメータマッチング**: Verify parameter placeholders match across languages / パラメータプレースホルダーが言語間で一致することを確認
- **Translation Updates** / **翻訳更新**: Keep translations current with new features / 新機能に合わせて翻訳を最新に保つ

### Quality Assurance / 品質保証
- **Native Speaker Review** / **ネイティブスピーカーレビュー**: Have native speakers review translations / ネイティブスピーカーに翻訳をレビューしてもらう
- **Context Testing** / **コンテキストテスト**: Test messages in actual bot usage scenarios / 実際のbot使用シナリオでメッセージをテスト
- **Cultural Sensitivity** / **文化的配慮**: Ensure messages are culturally appropriate / メッセージが文化的に適切であることを確認