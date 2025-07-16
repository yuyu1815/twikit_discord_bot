# discord.py 仕様書

## 概要

discord.pyは、PythonでDiscord APIを操作するための公式ライブラリです。Discord Botの開発やDiscordアプリケーションの作成に使用されます。

### 基本情報
- **ライブラリ名**: discord.py
- **開発者**: Rapptz
- **Context7 ID**: /rapptz/discord.py
- **信頼スコア**: 8.8/10
- **コードスニペット数**: 386
- **公式リポジトリ**: https://github.com/rapptz/discord.py

## インストール

```bash
pip install discord.py
```

### 必要な依存関係
- Python 3.8以上
- aiohttp
- websockets

## 主な機能

### 1. Bot開発機能
- Discord Botの作成と管理
- イベントハンドリング
- コマンドシステム
- スラッシュコマンド（Application Commands）

### 2. Discord API連携
- メッセージ送受信
- サーバー（Guild）管理
- チャンネル操作
- ユーザー管理
- 権限システム

### 3. 非同期処理
- asyncio基盤の非同期処理
- 効率的なAPI呼び出し
- イベントループ管理

## 基本的な使用方法

### 最小限のBot作成

```python
import discord

# インテントの設定（メッセージ内容を読み取るため）
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'ログインしました: {client.user}')

@client.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == client.user:
        return
    
    # $helloに反応
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

# Botを起動
client.run('YOUR_BOT_TOKEN')
```

### コマンドBot作成

```python
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.command()
async def test(ctx):
    await ctx.send('テストコマンドが実行されました！')

bot.run('YOUR_BOT_TOKEN')
```

## 主要クラスとメソッド

### Client クラス
Discord APIとの基本的な接続を管理するクラス

#### 主要メソッド
- `run(token)`: Botを起動
- `close()`: 接続を閉じる
- `get_guild(guild_id)`: ギルドを取得
- `get_user(user_id)`: ユーザーを取得
- `get_channel(channel_id)`: チャンネルを取得

### Bot クラス（commands.Bot）
コマンド機能を含む拡張されたClientクラス

#### 主要メソッド
- `add_command(command)`: コマンドを追加
- `remove_command(name)`: コマンドを削除
- `get_command(name)`: コマンドを取得
- `load_extension(name)`: 拡張機能をロード
- `unload_extension(name)`: 拡張機能をアンロード

### Message クラス
Discordメッセージを表現するクラス

#### 主要属性
- `content`: メッセージ内容
- `author`: 送信者
- `channel`: 送信チャンネル
- `guild`: 送信サーバー
- `created_at`: 作成日時

#### 主要メソッド
- `reply(content)`: 返信
- `edit(content)`: 編集
- `delete()`: 削除
- `add_reaction(emoji)`: リアクション追加

### Guild クラス
Discordサーバーを表現するクラス

#### 主要属性
- `name`: サーバー名
- `id`: サーバーID
- `owner`: サーバーオーナー
- `members`: メンバーリスト
- `channels`: チャンネルリスト

#### 主要メソッド
- `get_member(user_id)`: メンバー取得
- `get_channel(channel_id)`: チャンネル取得
- `get_role(role_id)`: ロール取得
- `fetch_member(user_id)`: メンバー取得（HTTP）

## イベントシステム

### 主要イベント

#### on_ready
Botがログインして準備完了時に発火

```python
@client.event
async def on_ready():
    print(f'{client.user}としてログインしました')
```

#### on_message
メッセージ受信時に発火

```python
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    print(f'{message.author}: {message.content}')
```

#### on_member_join
新しいメンバーがサーバーに参加時に発火

```python
@client.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send(f'{member.mention}さん、ようこそ！')
```

## コマンドシステム

### 基本的なコマンド作成

```python
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')
```

### 引数付きコマンド

```python
@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)
```

### コマンドコンバーター

```python
@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member}をキックしました')
```

## スラッシュコマンド（Application Commands）

### 基本的なスラッシュコマンド

```python
@bot.tree.command(name='hello', description='挨拶をします')
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message('こんにちは！')
```

### 引数付きスラッシュコマンド

```python
@bot.tree.command(name='echo', description='メッセージを繰り返します')
async def echo(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)
```

## 権限システム

### 権限チェック

```python
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
```

### カスタム権限チェック

```python
def is_owner():
    def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

@bot.command()
@is_owner()
async def shutdown(ctx):
    await ctx.send('シャットダウンします...')
    await bot.close()
```

## エラーハンドリング

### グローバルエラーハンドラー

```python
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('コマンドが見つかりません')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('権限が不足しています')
    else:
        await ctx.send(f'エラーが発生しました: {error}')
```

## Embed（埋め込み）メッセージ

### 基本的なEmbed作成

```python
embed = discord.Embed(
    title='タイトル',
    description='説明文',
    color=0x00ff00
)
embed.add_field(name='フィールド名', value='フィールド値', inline=False)
embed.set_footer(text='フッター')
embed.set_thumbnail(url='画像URL')

await ctx.send(embed=embed)
```

## ファイル送信

```python
# ローカルファイル送信
with open('image.png', 'rb') as f:
    picture = discord.File(f)
    await ctx.send(file=picture)

# テキストファイル作成して送信
import io
text = "ファイル内容"
file = discord.File(io.StringIO(text), filename='output.txt')
await ctx.send(file=file)
```

## Cog（拡張機能）システム

### Cog作成

```python
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def cog_command(self, ctx):
        await ctx.send('Cogからのコマンドです')
    
    @commands.Cog.listener()
    async def on_message(self, message):
        print(f'Cogでメッセージを受信: {message.content}')

# Cogをロード
async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

### Cogの管理

```python
# Cogをロード
await bot.load_extension('my_cog')

# Cogをアンロード
await bot.unload_extension('my_cog')

# Cogをリロード
await bot.reload_extension('my_cog')
```

## 非同期処理とタスク

### バックグラウンドタスク

```python
from discord.ext import tasks

@tasks.loop(seconds=60)
async def my_background_task():
    print('1分ごとに実行されます')

@my_background_task.before_loop
async def before_my_task():
    await bot.wait_until_ready()

# タスク開始
my_background_task.start()
```

## 設定とベストプラクティス

### 1. インテント設定
必要な権限のみを有効化

```python
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容読み取り
intents.members = True          # メンバー情報取得
```

### 2. トークン管理
環境変数やconfigファイルでトークンを管理

```python
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
```

### 3. エラーハンドリング
適切なエラーハンドリングを実装

### 4. レート制限対応
Discord APIのレート制限を考慮した実装

### 5. ログ出力
適切なログ出力でデバッグを容易に

```python
import logging

logging.basicConfig(level=logging.INFO)
```

## よくある問題と解決方法

### 1. インテント不足エラー
```
discord.errors.PrivilegedIntentsRequired
```
→ 必要なインテントを有効化

### 2. トークンエラー
```
discord.errors.LoginFailure
```
→ トークンの確認と再生成

### 3. 権限不足エラー
```
discord.errors.Forbidden
```
→ Bot権限の確認と設定

## 参考リンク

- [公式ドキュメント](https://discordpy.readthedocs.io/)
- [GitHub リポジトリ](https://github.com/rapptz/discord.py)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord API ドキュメント](https://discord.com/developers/docs)

## 更新履歴

- 2025-07-17: 初版作成（Context7データベースより）

---

この仕様書は、discord.pyライブラリの包括的なガイドとして作成されました。実際の開発では、公式ドキュメントと併せてご利用ください。