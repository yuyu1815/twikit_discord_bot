# RSS-free tweet acquisition discord bot
![banner](./img/Twitter.jpg)
[英語](./README.md) 日本語

これまでRSSを使ったツイートを取得する方法しかありませんでしたが
Twitterのアカウントを使うことによりそれを克服しました
## 目次
- [特徴](#特徴)
- [進行中](#現在進行中)
- [インストール](#インストール方法)
- [設定](#設定)
- [コマンド](#コマンドできること)
## 特徴

- お金がかからないツイートの自動取得
- 複数のサーバー、チャンネルに対応
-  自動fxtwitter,fxtiktokに変換

## 現在進行中

 - [ ] アリエクに対応
 - [ ] fxtwitterをフォークし独自に改造

## インストール方法

プロジェクトのインストール手順を記載します。
Linux or Mac
```bash
 start.sh
```
Windows
```bash
 start.bat
```
### 設定
[sample.env](./src/sample.env)

以下の2つを設定してください
```dotenv
TOKEN="Discord_token"
#support ja_JP en_US zh_CN
Languages="en_US"
```
開始方法
Linux or Mac
```bash
cd src 
python3 Bot.py
```
Windows
```bash
cd src
py Bot.py
```
Discordのセットアップ
以下の設定で招待をしてください
![discord](./img/Setup_2.png)
## コマンド&できること
```

```

![command](img/set_command.png)
- そのチャンネルの名前の人の自動投稿を削除
![command](img/del_command.png)
- 自動投稿
![command](img/auto_say.png)
- 現在の設定の表示
- ![command](img/check_command.png)
- fxtwitterに変換機能の On OFF
![command](img/Command_1.png)
