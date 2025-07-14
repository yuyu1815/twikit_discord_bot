# RSS-free tweet acquisition discord bot
![banner](./img/Twitter.jpg)
[英語](README.md) [中文](README_zh.md) 日本語

これまでRSSを使ったツイートを取得する方法しかありませんでしたが、Twitterのアカウントを使うことによりそれを克服しました。

## 目次
- [特徴](#特徴)
- [進行中](#現在進行中)
- [インストール](#インストール方法)
- [設定](#設定)
- [コマンド](#コマンドできること)

## 特徴

- お金がかからないツイートの自動取得
- 複数のサーバー、チャンネルに対応
- 自動fxtwitter、fxtiktok URLに変換
- データベースベースの設定保存
- 多言語サポート（英語、日本語、中国語）

## 現在進行中

 - [ ] アリエクに対応
 - [ ] fxtwitterをフォークし独自に改造

## インストール方法

プロジェクトのインストール手順を記載します。

### 前提条件
- Python 3.8以上
- Discord Bot Token

### 依存関係のインストール
Linux or Mac
```bash
python3 -m pip install -r requirements.txt
```
Windows
```bash
pip install -r requirements.txt
```

## 設定

### 1. Twitter Cookie設定
1. この[Chrome拡張機能](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)をインストールしてください。
2. 以下の画像のようにしてcookieをコピーしてください。
![image](./img/cookie.png)
3. コピーしたcookieを`data/`ディレクトリ内に`cookie.json`という名前で保存してください。

### 2. 環境変数
プロジェクトルートに`.env`ファイルを作成し、以下の設定を行ってください：
```dotenv
TOKEN="あなたのDiscord_Bot_Token"
# サポート言語: ja_JP, en_US, zh_CN
Languages="ja_JP"
```

### 3. Discord Bot設定
以下の権限でボットを招待してください：
![discord](./img/Setup_2.png)
![discord](./img/Setup_3.png)

### 4. 開始方法
Linux or Mac
```bash
python3 main.py
```
Windows
```bash
python main.py
```

## コマンド&できること

### Twitter フィード管理
- **チャンネルにTwitterフィードを追加**
```
/set_twitter twitter_user_name: <ユーザー名>
```
![command](img/set_command.png)

- **チャンネルからTwitterフィードを削除**
```
/del_twitter user_name: <ユーザー名>
```
![command](img/del_command.png)

### 設定管理
- **Twitter更新のクールダウン時間を設定**
```
/check-time minutes: <分数>
```
![command](img/time_command.png)

- **Twitter更新のオン/オフ切り替え**
```
/change-setting-twitter-get mode: <true/false>
```

- **URLプレビュー変換のオン/オフ切り替え**
```
/change-setting-url-preview mode: <true/false>
```
![command](img/command_1.png)

- **現在の設定を表示**
```
/check-settings
```
![command](img/check_command.png)

### 自動機能
- **自動Twitter投稿**
![command](img/auto_say.png)

- **自動URL変換** - Twitter/XとTikTokのURLをfxtwitter/fxtiktokに変換してより良い埋め込み表示を提供

## プロジェクト構造
```
twikit_discord_bot/
├── data/                     # アプリケーションデータファイル
│   ├── cookie.json          # Twitter認証クッキー
│   ├── cookie_edit.json     # バックアップクッキーファイル
│   ├── DiscordSetting.json  # Discordサーバー設定
│   └── Twitter_msg.json     # Twitterメッセージキャッシュ
├── src/
│   ├── cogs/                # Discordコマンドモジュール
│   │   ├── twitter_commands.py  # Twitter関連スラッシュコマンド
│   │   └── url_fixer.py         # URL置換機能
│   ├── core/                # コアボット機能
│   │   ├── bot.py           # メインボットクラスとイベントハンドラ
│   │   ├── database.py      # データベース操作
│   │   └── twitter_client.py    # Twitter APIクライアント
│   ├── config/              # 設定管理
│   │   └── settings.py      # 設定とファイルI/O操作
│   └── lang/                # 言語ファイル
│       ├── en_US.json       # 英語翻訳
│       ├── ja_JP.json       # 日本語翻訳
│       └── zh_CN.json       # 中国語翻訳
├── main.py                  # アプリケーションエントリーポイント
├── requirements.txt         # Python依存関係
└── .env                     # 環境変数
```
