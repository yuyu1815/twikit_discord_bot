# ツイート取得機能のRSS化 技術定義書

## 1. はじめに

本技術定義書は、現在のDiscord BotにおけるTwitterツイート取得機能を、標準的なRSSフィードとして独立させるための技術的な要件と設計を記述するものです。これにより、ツイートの更新を外部のRSSリーダーや他のシステムから容易に購読できるようになり、機能のモジュール化と再利用性の向上が期待されます。

## 2. 現行システム概要

現在のツイート取得機能は、`twikit`ライブラリとカスタムのクライアント管理（`TwitterClientManager`）を用いて、特定のユーザーの最新ツイートを取得しています。主要なコンポーネントは以下の通りです。

-   `src/core/twitter_client.py`: `twikit`クライアントの初期化、クッキーのロード、各種Twitter API操作（ユーザーツイート取得、リツイート判定、URL抽出など）をカプセル化しています。
-   `src/core/twitter_client_manager.py`: 認証済みクライアントとゲストクライアントの管理、およびAPI呼び出し時のフォールバックロジックを提供します。`get_rss_client`メソッドは、RSSフィード取得のために認証済みクライアントを返します。
-   `src/core/twitter_analyzer.py`: `get_rss_like_tweets`関数が、`TwitterClientManager`を介して特定のユーザーの最新ツイートをリスト形式で取得します。

## 3. 提案するRSSシステムアーキテクチャ

ツイート取得機能をRSS化するために、以下のアーキテクチャを提案します。

### 3.1. コアコンポーネント

-   **RSSジェネレーターモジュール**: 新たに`src/rss/rss_generator.py`のようなモジュールを作成し、`Tweet`オブジェクトのリストを標準的なRSS 2.0 XML形式に変換する責務を担います。

### 3.2. データソース

-   既存の`src/core/twitter_analyzer.py`内の`get_rss_like_tweets`関数をデータソースとして活用します。この関数は、指定されたユーザーの最新ツイートを`Tweet`オブジェクトのリストとして返します。

### 3.3. RSSフィード生成ロジック

1.  **ツイート取得**: `get_rss_like_tweets`を呼び出し、対象ユーザーの最新ツイートを取得します。
2.  **RSSアイテムへのマッピング**: 取得した各`Tweet`オブジェクトをRSSフィードの`<item>`要素にマッピングします。
3.  **XML生成**: マッピングされたデータを使用して、RSS 2.0の仕様に準拠したXMLを生成します。
4.  **ファイル保存**: 生成されたXMLを、ユーザー名に基づいたファイル名で指定されたディレクトリに保存します。

### 3.4. エンドポイント/公開方法

Discord Botの性質上、Webサーバーを立てることは現時点では想定しません。RSSフィードの更新は、Discordコマンドからのリクエストをトリガーとして行われます。

-   **Discordコマンド**: 新たに`generate_rss`のようなDiscordコマンドを導入します。このコマンドが実行されると、指定されたTwitterユーザーのRSSフィードが生成または更新され、指定されたパスにファイルとして出力されます。コマンドの応答として、生成されたRSSファイルのパス（またはURL）をユーザーに提供することを検討します。
-   **ファイル出力**: 各TwitterユーザーのRSS XMLファイルを、`data/rss_feeds/{twitter_user_name}.xml`のようなパスに生成します。これにより、外部のRSSリーダーがこのファイルを直接読み込むことが可能になります。

### 3.5. スケジューリングとクールダウン

-   RSSフィードの更新は、Discordコマンドによってトリガーされます。定期的な自動更新は行いません。
-   **ユーザーごとのクールダウン**: 各TwitterユーザーのRSSフィード更新には、5分間のクールダウンを設けます。これは、前回の更新からの経過時間を記録し、5分が経過していない場合は更新をスキップすることで実現します。このクールダウン情報は、ボットのメモリまたは永続ストレージ（例: データベース）で管理します。
-   **クールダウン中の応答**: クールダウン期間中に更新リクエストがあった場合、新たにツイートを取得・生成する代わりに、**既に生成されている最新のRSSファイルを返します。**

## 4. 技術詳細

### 4.1. RSS 2.0 XML構造

生成されるRSSフィードは、RSS 2.0の仕様に準拠します。主要な要素は以下の通りです。

```xml
<rss version="2.0">
  <channel>
    <title>ユーザー名 のツイート</title>
    <link>https://twitter.com/ユーザー名</link>
    <description>ユーザー名 の最新ツイート</description>
    <language>ja</language> <!-- または en-US など -->
    <lastBuildDate>Wed, 16 Jul 2025 12:00:00 GMT</lastBuildDate>
    <item>
      <title>ツイートのテキスト（短縮版または最初の行）</title>
      <link>https://twitter.com/ユーザー名/status/ツイートID</link>
      <description><![CDATA[ツイートの全文]]></description>
      <pubDate>Wed, 16 Jul 2025 11:55:00 GMT</pubDate>
      <guid isPermaLink="true">https://twitter.com/ユーザー名/status/ツイートID</guid>
      <author>ユーザー名@twitter.com</author>
    </item>
    <!-- 他のツイートアイテム -->
  </channel>
</rss>
```

### 4.2. `Tweet`オブジェクトからRSSアイテムへのマッピング

| `Tweet`オブジェクトのフィールド | RSS `<item>`要素 | 説明 |
| :---------------------------- | :---------------- | :--- |
| `tweet.text`                  | `<title>`         | ツイートのテキスト。長すぎる場合は適宜短縮。 |
| `tweet.full_text`             | `<description>`   | ツイートの全文。CDATAセクションで囲む。 |
| `tweet.id`                    | `<link>`          | `https://twitter.com/{user.screen_name}/status/{tweet.id}`形式のURL。 |
| `tweet.id`                    | `<guid>`          | `<link>`と同じ。`isPermaLink="true"`を設定。 |
| `tweet.created_at`            | `<pubDate>`       | ツイートの作成日時。RFC 822形式に変換。 |
| `tweet.user.screen_name`      | `<author>`        | `{user.screen_name}@twitter.com`形式。 |

### 4.3. エラーハンドリング

-   ツイート取得時のエラー（API制限、ネットワークエラーなど）は、既存の`TwitterClientManager`のエラーハンドリングに準じ、ログに記録します。
-   RSS XML生成時のエラーは、適切な例外処理を行い、ログに記録します。
-   RSSファイルへの書き込みエラーも同様に処理します。
-   クールダウン中のリクエストは、ユーザーにその旨を通知し、**既存のRSSファイルのパスを返します。**

### 4.4. 設定

以下の設定項目を`src/config/settings.py`に追加することを検討します。

-   `RSS_FEED_OUTPUT_DIR`: 生成されるRSS XMLファイルの出力ディレクトリ（例: `data/rss_feeds`）。
-   `RSS_FEED_COOLDOWN_MINUTES`: RSSフィード更新のクールダウン時間（分）。デフォルトは5分。
-   `RSS_FEED_MAX_TWEETS`: RSSフィードに含めるツイートの最大数。

## 5. 実装ステップ（高レベル）

1.  **`rss_generator.py`の作成**:
    *   `src/rss/`ディレクトリ内に`rss_generator.py`を作成します。
    *   `Tweet`オブジェクトのリストとユーザー情報を引数に取り、RSS 2.0 XML文字列を返す関数を実装します。
    *   `xml.etree.ElementTree`または`lxml`などのXMLライブラリを使用します。
2.  **設定の追加**:
    *   `src/config/settings.py`に上記4.4で定義した設定項目を追加します。
3.  **Discordコマンドの追加**:
    *   `src/cogs/twitter_commands.py`に、`generate_rss`のような新しいコマンドを追加します。
    *   このコマンドは、引数としてTwitterユーザー名を受け取ります。
    *   コマンド実行時に、クールダウンをチェックし、クールダウン期間中でない場合は、`get_rss_like_tweets`を呼び出してツイートを取得し、`rss_generator.py`を使用してRSS XMLを生成し、`RSS_FEED_OUTPUT_DIR`に`{twitter_user_name}.xml`として保存します。
    *   **クールダウン期間中の場合は、ユーザーにその旨を通知し、既存のRSSファイルのパスを返します。**
    *   生成されたRSSファイルのパスをユーザーに返します。
4.  **ボットロジックの変更**:
    *   `src/core/bot.py`から定期的なツイートチェックタスク（`check_for_new_tweets_periodically`）を削除します。
    *   ユーザーごとの最終更新時刻を管理するための辞書（例: `self.last_rss_update_times = {}`）を`MyBot`クラスに追加します。
5.  **RSS出力ディレクトリの作成**: `data/rss_feeds`ディレクトリが存在しない場合は作成するロジックを追加します（例: ボット起動時）。
6.  **テスト**:
    *   RSSフィードが正しく生成されるか、XMLが有効であるかを確認する単体テストおよび統合テストを作成します。
    *   クールダウン機能が正しく動作するかを確認するテストを作成します。

## 6. 今後の検討事項

-   **複数ユーザーのRSSフィード**: 現在は単一ユーザーのRSS化を想定していますが、将来的には複数のユーザーのフィードを管理・生成する機能の追加。
-   **RSSフィードのカスタマイズ**: ユーザーがRSSフィードに含めるツイートの種類（リプライを除く、メディアのみなど）を選択できるオプションの追加。
-   **Webサーバーの導入**: より高度なRSS配信のために、軽量なWebサーバーを組み込む検討。
-   **クールダウン情報の永続化**: ボットの再起動時にクールダウン情報が失われないよう、データベースなどに保存する検討。