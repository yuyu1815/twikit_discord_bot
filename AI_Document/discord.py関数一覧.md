# discord.py 関数一覧

## 概要

このドキュメントは、discord.pyライブラリの主要な関数とメソッドの包括的な一覧です。各クラスのメソッドと関数を機能別に整理して掲載しています。

## 基本情報
- **ライブラリ名**: discord.py
- **バージョン**: 2.x系
- **公式ドキュメント**: https://discordpy.readthedocs.io/

## 主要クラス

### Client クラス
Discord APIとの基本的な接続を管理するクラス

#### 接続・認証関連
- `run(token, *, reconnect=True)` - Botを起動
- `start(token, *, reconnect=True)` - 非同期でBotを起動
- `close()` - 接続を閉じる
- `login(token)` - ログイン処理
- `logout()` - ログアウト処理

#### データ取得メソッド
- `get_guild(guild_id)` - ギルドを取得
- `get_user(user_id)` - ユーザーを取得
- `get_channel(channel_id)` - チャンネルを取得
- `get_emoji(emoji_id)` - 絵文字を取得
- `get_sticker(sticker_id)` - ステッカーを取得

#### 非同期データ取得メソッド
- `fetch_guild(guild_id)` - ギルドを非同期取得
- `fetch_user(user_id)` - ユーザーを非同期取得
- `fetch_channel(channel_id)` - チャンネルを非同期取得
- `fetch_invite(url)` - 招待リンクを非同期取得
- `fetch_template(code)` - テンプレートを非同期取得

#### ユーティリティメソッド
- `wait_until_ready()` - Bot準備完了まで待機
- `wait_for(event, *, check=None, timeout=None)` - イベント待機
- `is_ready()` - Bot準備状態を確認
- `is_closed()` - 接続状態を確認

### Bot クラス (commands.Bot)
コマンド機能を含む拡張されたClientクラス

#### コマンド管理
- `add_command(command)` - コマンドを追加
- `remove_command(name)` - コマンドを削除
- `get_command(name)` - コマンドを取得
- `walk_commands()` - 全コマンドを反復処理
- `command(*args, **kwargs)` - コマンドデコレータ
- `group(*args, **kwargs)` - グループコマンドデコレータ

#### 拡張機能管理
- `load_extension(name)` - 拡張機能をロード
- `unload_extension(name)` - 拡張機能をアンロード
- `reload_extension(name)` - 拡張機能をリロード
- `add_cog(cog)` - Cogを追加
- `remove_cog(name)` - Cogを削除
- `get_cog(name)` - Cogを取得

#### コマンド処理
- `invoke(ctx)` - コマンドを実行
- `process_commands(message)` - コマンドを処理
- `get_context(message, *, cls=Context)` - コンテキストを取得

### Message クラス
Discordメッセージを表現するクラス

#### 基本属性
- `id` - メッセージID
- `content` - メッセージ内容
- `author` - 送信者
- `channel` - 送信チャンネル
- `guild` - 送信サーバー
- `created_at` - 作成日時
- `edited_at` - 編集日時

#### メッセージ操作
- `edit(content=None, *, embed=None, embeds=None)` - メッセージを編集
- `delete(*, delay=None)` - メッセージを削除
- `pin()` - メッセージをピン留め
- `unpin()` - ピン留めを解除
- `reply(content=None, **kwargs)` - 返信
- `add_reaction(emoji)` - リアクションを追加
- `remove_reaction(emoji, member)` - リアクションを削除
- `clear_reactions()` - 全リアクションを削除

### Guild クラス
Discordサーバーを表現するクラス

#### 基本属性
- `id` - サーバーID
- `name` - サーバー名
- `owner` - サーバーオーナー
- `members` - メンバーリスト
- `channels` - チャンネルリスト
- `roles` - ロールリスト

#### メンバー管理
- `get_member(user_id)` - メンバーを取得
- `fetch_member(user_id)` - メンバーを非同期取得
- `ban(user, **kwargs)` - ユーザーをBAN
- `unban(user)` - BANを解除
- `kick(user, **kwargs)` - ユーザーをキック

#### チャンネル管理
- `get_channel(channel_id)` - チャンネルを取得
- `create_text_channel(name, **kwargs)` - テキストチャンネルを作成
- `create_voice_channel(name, **kwargs)` - ボイスチャンネルを作成
- `create_category(name, **kwargs)` - カテゴリを作成

#### ロール管理
- `get_role(role_id)` - ロールを取得
- `create_role(**kwargs)` - ロールを作成

### User クラス
Discordユーザーを表現するクラス

#### 基本属性
- `id` - ユーザーID
- `name` - ユーザー名
- `discriminator` - 識別子
- `avatar` - アバター
- `bot` - Bot判定
- `created_at` - アカウント作成日時

#### ユーザー操作
- `send(content=None, **kwargs)` - DMを送信
- `create_dm()` - DMチャンネルを作成

### TextChannel クラス
テキストチャンネルを表現するクラス

#### メッセージ送信
- `send(content=None, **kwargs)` - メッセージを送信
- `trigger_typing()` - タイピング表示を開始
- `typing()` - タイピングコンテキストマネージャー

#### メッセージ取得
- `fetch_message(message_id)` - メッセージを取得
- `history(**kwargs)` - メッセージ履歴を取得
- `pins()` - ピン留めメッセージを取得

#### チャンネル管理
- `edit(**kwargs)` - チャンネルを編集
- `delete()` - チャンネルを削除
- `set_permissions(target, **kwargs)` - 権限を設定

## イベント関数

### 基本イベント
- `on_ready()` - Bot準備完了時
- `on_resumed()` - 接続再開時
- `on_error(event, *args, **kwargs)` - エラー発生時
- `on_socket_event_type(event_type)` - ソケットイベント受信時

### メッセージイベント
- `on_message(message)` - メッセージ受信時
- `on_message_delete(message)` - メッセージ削除時
- `on_message_edit(before, after)` - メッセージ編集時
- `on_reaction_add(reaction, user)` - リアクション追加時
- `on_reaction_remove(reaction, user)` - リアクション削除時
- `on_reaction_clear(message, reactions)` - リアクション全削除時

### メンバーイベント
- `on_member_join(member)` - メンバー参加時
- `on_member_remove(member)` - メンバー退出時
- `on_member_update(before, after)` - メンバー情報更新時
- `on_member_ban(guild, user)` - メンバーBAN時
- `on_member_unban(guild, user)` - BAN解除時

### ギルドイベント
- `on_guild_join(guild)` - サーバー参加時
- `on_guild_remove(guild)` - サーバー退出時
- `on_guild_update(before, after)` - サーバー情報更新時
- `on_guild_role_create(role)` - ロール作成時
- `on_guild_role_delete(role)` - ロール削除時
- `on_guild_role_update(before, after)` - ロール更新時

### チャンネルイベント
- `on_guild_channel_create(channel)` - チャンネル作成時
- `on_guild_channel_delete(channel)` - チャンネル削除時
- `on_guild_channel_update(before, after)` - チャンネル更新時

### ボイスイベント
- `on_voice_state_update(member, before, after)` - ボイス状態更新時

## コマンドシステム

### コマンドデコレータ
- `@bot.command(name=None, **kwargs)` - コマンド定義
- `@bot.group(name=None, **kwargs)` - グループコマンド定義
- `@commands.command(**kwargs)` - Cogでのコマンド定義

### コマンドチェック
- `@commands.has_permissions(**perms)` - 権限チェック
- `@commands.has_role(role)` - ロールチェック
- `@commands.has_any_role(*roles)` - 複数ロールチェック
- `@commands.is_owner()` - オーナーチェック
- `@commands.guild_only()` - サーバー限定
- `@commands.dm_only()` - DM限定
- `@commands.check(predicate)` - カスタムチェック

### コマンドエラー
- `CommandError` - 基本コマンドエラー
- `CommandNotFound` - コマンド未発見
- `MissingRequiredArgument` - 必須引数不足
- `BadArgument` - 不正な引数
- `MissingPermissions` - 権限不足
- `BotMissingPermissions` - Bot権限不足

## Application Commands (スラッシュコマンド)

### app_commands モジュール
- `@app_commands.command()` - スラッシュコマンド定義
- `@app_commands.describe(**kwargs)` - パラメータ説明
- `@app_commands.choices(**kwargs)` - 選択肢定義
- `@app_commands.guild_only()` - サーバー限定
- `@app_commands.default_permissions(**kwargs)` - デフォルト権限

### CommandTree クラス
- `sync(*, guild=None)` - コマンドを同期
- `add_command(command, *, guild=None)` - コマンドを追加
- `remove_command(command, *, guild=None)` - コマンドを削除
- `get_command(name, *, guild=None)` - コマンドを取得

## UI コンポーネント

### View クラス
- `add_item(item)` - アイテムを追加
- `remove_item(item)` - アイテムを削除
- `clear_items()` - 全アイテムを削除
- `stop()` - ビューを停止
- `wait()` - ビュー完了まで待機

### Button クラス
- `callback(interaction)` - ボタンクリック時のコールバック
- `disabled` - 無効化状態
- `label` - ボタンラベル
- `style` - ボタンスタイル
- `emoji` - ボタン絵文字

### Select クラス
- `callback(interaction)` - 選択時のコールバック
- `options` - 選択肢リスト
- `placeholder` - プレースホルダー
- `min_values` - 最小選択数
- `max_values` - 最大選択数

## Embed クラス

### 基本メソッド
- `add_field(name, value, *, inline=True)` - フィールドを追加
- `insert_field_at(index, name, value, *, inline=True)` - フィールドを挿入
- `remove_field(index)` - フィールドを削除
- `set_field_at(index, name, value, *, inline=True)` - フィールドを設定
- `clear_fields()` - 全フィールドを削除

### 設定メソッド
- `set_author(name, *, url=None, icon_url=None)` - 作成者を設定
- `set_footer(text, *, icon_url=None)` - フッターを設定
- `set_image(url)` - 画像を設定
- `set_thumbnail(url)` - サムネイルを設定
- `to_dict()` - 辞書に変換

## ファイル操作

### File クラス
- `File(fp, filename=None, *, description=None, spoiler=False)` - ファイル作成

## ユーティリティ関数

### discord モジュール関数
- `utils.get(iterable, **attrs)` - 属性でオブジェクトを検索
- `utils.find(predicate, iterable)` - 条件でオブジェクトを検索
- `utils.oauth_url(client_id, *, permissions=None, guild=None)` - OAuth URLを生成
- `utils.snowflake_time(id)` - SnowflakeからDatetimeを取得
- `utils.time_snowflake(datetime_obj)` - DatetimeからSnowflakeを生成

### 権限関連
- `Permissions(**kwargs)` - 権限オブジェクト作成
- `PermissionOverwrite(**kwargs)` - 権限上書きオブジェクト作成

## 例外クラス

### 基本例外
- `DiscordException` - 基本例外
- `ClientException` - クライアント例外
- `LoginFailure` - ログイン失敗
- `HTTPException` - HTTP例外
- `Forbidden` - 権限不足
- `NotFound` - リソース未発見
- `DiscordServerError` - サーバーエラー

### コマンド例外
- `CommandError` - コマンドエラー
- `CommandNotFound` - コマンド未発見
- `MissingRequiredArgument` - 必須引数不足
- `TooManyArguments` - 引数過多
- `BadArgument` - 不正引数
- `CheckFailure` - チェック失敗

## 更新履歴

- 2025-07-17: 初版作成
  - 主要クラスとメソッドの包括的な一覧を作成
  - イベント関数、コマンドシステム、UI コンポーネントを網羅
  - 実用的な関数分類と説明を追加

---

この関数一覧は、discord.pyライブラリの開発において、必要な関数やメソッドを素早く見つけるためのリファレンスとして活用してください。