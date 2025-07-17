# RSS Directory / RSSディレクトリ

## Overview / 概要

This directory contains RSS feed generation functionality for the Twikit Discord Bot. It provides the ability to convert Twitter feeds into standard RSS 2.0 XML format, enabling users to consume Twitter content through RSS readers.

このディレクトリには、Twikit Discord BotのRSSフィード生成機能が含まれています。TwitterフィードをスタンダードなRSS 2.0 XML形式に変換する機能を提供し、ユーザーがRSSリーダーを通じてTwitterコンテンツを消費できるようにします。

## Files / ファイル

### rss_generator.py
Contains the `RSSGenerator` class that converts tweet lists to RSS 2.0 XML format.

ツイートリストをRSS 2.0 XML形式に変換する `RSSGenerator` クラスが含まれています。

## Key Features / 主な機能

### RSS 2.0 Compliance / RSS 2.0準拠
- **Standard Format** / **標準フォーマット**: Generates valid RSS 2.0 XML / 有効なRSS 2.0 XMLを生成
- **Channel Information** / **チャンネル情報**: Includes proper channel metadata / 適切なチャンネルメタデータを含む
- **Item Structure** / **アイテム構造**: Each tweet becomes a properly formatted RSS item / 各ツイートが適切にフォーマットされたRSSアイテムになる

### Tweet Processing / ツイート処理
- **URL-Only Content** / **URLのみのコンテンツ**: Focuses on tweet URLs rather than full content / 完全なコンテンツではなくツイートURLに焦点を当てる
- **Tweet Limitation** / **ツイート制限**: Configurable maximum number of tweets (default: 5) / 設定可能な最大ツイート数（デフォルト：5）
- **Chronological Order** / **時系列順**: Maintains tweet order from newest to oldest / 最新から最古へのツイート順序を維持

### File Management / ファイル管理
- **Automatic Directory Creation** / **自動ディレクトリ作成**: Creates output directories if they don't exist / 存在しない場合は出力ディレクトリを作成
- **User-Specific Files** / **ユーザー固有ファイル**: Generates separate RSS files for each Twitter user / 各Twitterユーザーに対して個別のRSSファイルを生成
- **UTF-8 Encoding** / **UTF-8エンコーディング**: Proper Unicode support for international content / 国際コンテンツの適切なUnicodeサポート

## Class Structure / クラス構造

### RSSGenerator Class / RSSGeneratorクラス

#### Constructor / コンストラクタ
```python
def __init__(self, output_dir: str = "data/rss_feeds", max_tweets: int = 5)
```

**Parameters / パラメータ:**
- `output_dir` - RSS XML files output directory / RSS XMLファイルの出力ディレクトリ
- `max_tweets` - Maximum number of tweets to include (capped at 5) / 含める最大ツイート数（5に制限）

#### Methods / メソッド

##### generate_rss()
```python
def generate_rss(self, tweets: List[Tweet], screen_name: str) -> str
```
Generates RSS XML from a list of tweets and returns it as a string.

ツイートのリストからRSS XMLを生成し、文字列として返します。

**Parameters / パラメータ:**
- `tweets` - List of tweet objects / ツイートオブジェクトのリスト
- `screen_name` - Twitter username / Twitterユーザー名

**Returns / 戻り値:**
- RSS XML as string / 文字列としてのRSS XML

##### save_rss()
```python
def save_rss(self, tweets: List[Tweet], screen_name: str) -> str
```
Generates RSS XML and saves it to a file.

RSS XMLを生成してファイルに保存します。

**Parameters / パラメータ:**
- `tweets` - List of tweet objects / ツイートオブジェクトのリスト
- `screen_name` - Twitter username / Twitterユーザー名

**Returns / 戻り値:**
- Path of the saved file / 保存されたファイルのパス

## RSS Structure / RSS構造

The generated RSS follows this structure:

生成されるRSSは以下の構造に従います：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{screen_name} のツイート</title>
        <link>https://twitter.com/{screen_name}</link>
        <description>{screen_name} の最新ツイート</description>
        <language>ja</language>
        <lastBuildDate>{current_date}</lastBuildDate>
        
        <item>
            <title>Tweet {tweet_id}</title>
            <link>https://twitter.com/{screen_name}/status/{tweet_id}</link>
            <guid isPermaLink="true">https://twitter.com/{screen_name}/status/{tweet_id}</guid>
        </item>
        <!-- More items... -->
    </channel>
</rss>
```

### Channel Elements / チャンネル要素
- **title** / **タイトル**: `{screen_name} のツイート` format / `{screen_name} のツイート` 形式
- **link** / **リンク**: Direct link to Twitter profile / Twitterプロフィールへの直接リンク
- **description** / **説明**: `{screen_name} の最新ツイート` format / `{screen_name} の最新ツイート` 形式
- **language** / **言語**: Set to "ja" (Japanese) by default / デフォルトで"ja"（日本語）に設定
- **lastBuildDate** / **最終構築日**: Current timestamp when RSS was generated / RSSが生成された現在のタイムスタンプ

### Item Elements / アイテム要素
- **title** / **タイトル**: `Tweet {tweet_id}` format / `Tweet {tweet_id}` 形式
- **link** / **リンク**: Direct URL to the specific tweet / 特定のツイートへの直接URL
- **guid** / **GUID**: Permanent link to the tweet (same as link) / ツイートへの永続リンク（リンクと同じ）

## Usage Examples / 使用例

### Basic RSS Generation / 基本的なRSS生成
```python
from src.rss.rss_generator import RSSGenerator
from twikit.tweet import Tweet

# Initialize RSS generator
rss_gen = RSSGenerator(output_dir="data/rss_feeds", max_tweets=5)

# Generate RSS XML string
tweets = [...]  # List of Tweet objects
xml_content = rss_gen.generate_rss(tweets, "username")
print(xml_content)
```

### Save RSS to File / RSSをファイルに保存
```python
# Save RSS to file
file_path = rss_gen.save_rss(tweets, "username")
print(f"RSS saved to: {file_path}")
# Output: RSS saved to: data/rss_feeds/username.xml
```

### Custom Configuration / カスタム設定
```python
# Custom output directory and tweet limit
custom_rss_gen = RSSGenerator(
    output_dir="custom/rss/path",
    max_tweets=3
)

# Generate with custom settings
file_path = custom_rss_gen.save_rss(tweets, "username")
```

## Integration with Bot Commands / Botコマンドとの統合

The RSS generator is integrated with the Discord bot through the `/generate_rss` command in `TwitterCommandsCog`:

RSSジェネレーターは、`TwitterCommandsCog` の `/generate_rss` コマンドを通じてDiscord botと統合されています：

```python
@app_commands.command(name="generate_rss")
async def generate_rss(self, interaction: discord.Interaction, twitter_user_name: str):
    # Fetch tweets for the user
    tweets = await get_rss_like_tweets_with_manager(manager, twitter_user_name, count=5)
    
    # Generate RSS
    rss_generator = RSSGenerator()
    file_path = rss_generator.save_rss(tweets, twitter_user_name)
    
    # Send file to Discord
    await interaction.followup.send(file=discord.File(file_path))
```

## File Output / ファイル出力

### Default Location / デフォルトの場所
RSS files are saved to `data/rss_feeds/` by default:

RSSファイルはデフォルトで `data/rss_feeds/` に保存されます：

```
data/
└── rss_feeds/
    ├── username1.xml
    ├── username2.xml
    └── username3.xml
```

### File Naming / ファイル命名
- **Format** / **フォーマット**: `{screen_name}.xml`
- **Example** / **例**: `elonmusk.xml`, `twitter.xml`
- **Encoding** / **エンコーディング**: UTF-8 with BOM for compatibility / 互換性のためのBOM付きUTF-8

## Technical Specifications / 技術仕様

### XML Processing / XML処理
- **Library** / **ライブラリ**: Uses Python's built-in `xml.etree.ElementTree` / Pythonの組み込み `xml.etree.ElementTree` を使用
- **Formatting** / **フォーマット**: Automatic indentation with `ET.indent()` (Python 3.9+) / `ET.indent()` による自動インデント（Python 3.9以上）
- **Validation** / **検証**: Generates valid RSS 2.0 XML / 有効なRSS 2.0 XMLを生成

### Performance Considerations / パフォーマンス考慮事項
- **Memory Efficient** / **メモリ効率**: Processes tweets in memory without large buffers / 大きなバッファなしでメモリ内でツイートを処理
- **File I/O** / **ファイルI/O**: Single write operation per RSS file / RSSファイルごとに単一の書き込み操作
- **Tweet Limit** / **ツイート制限**: Hard limit of 5 tweets to prevent large files / 大きなファイルを防ぐための5ツイートのハード制限

## Dependencies / 依存関係

- `xml.etree.ElementTree` - XML processing / XML処理
- `email.utils.formatdate` - RFC 2822 date formatting / RFC 2822日付フォーマット
- `pathlib.Path` - File path operations / ファイルパス操作
- `typing` - Type hints / 型ヒント
- `twikit.tweet.Tweet` - Tweet object structure / ツイートオブジェクト構造

## Error Handling / エラーハンドリング

The RSS generator includes basic error handling for:

RSSジェネレーターには以下の基本的なエラーハンドリングが含まれています：

- **Directory Creation** / **ディレクトリ作成**: Handles permission and path errors / 権限とパスエラーを処理
- **File Writing** / **ファイル書き込み**: Manages disk space and permission issues / ディスク容量と権限の問題を管理
- **XML Generation** / **XML生成**: Validates tweet data before processing / 処理前にツイートデータを検証

## Future Enhancements / 将来の拡張

Potential improvements for the RSS functionality:

RSS機能の潜在的な改善：

- **Content Inclusion** / **コンテンツ包含**: Option to include tweet text content / ツイートテキストコンテンツを含むオプション
- **Media Support** / **メディアサポート**: Include images and videos in RSS items / RSSアイテムに画像と動画を含む
- **Custom Templates** / **カスタムテンプレート**: Configurable RSS templates / 設定可能なRSSテンプレート
- **Atom Support** / **Atomサポート**: Generate Atom feeds in addition to RSS / RSSに加えてAtomフィードを生成