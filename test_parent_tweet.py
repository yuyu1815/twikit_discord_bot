import asyncio
from twikit.guest import GuestClient

# --- 設定 ---
# テストに使用するツイートID
# 親ツイート: https://x.com/X/status/1788204335225454629
PARENT_TWEET_ID = "1944401404816200173"
# ↑への返信ツイート: https://x.com/3blue1brown/status/1788222393047924938
REPLY_TWEET_ID = "1944402996160540687"
# リツイート: https://x.com/X/status/1808833753475321963 (元ツイートは https://x.com/SpaceX/status/1808831442914750700)
RETWEET_ID = "1924465040759087252"

# --- ここから下は編集不要です ---

async def get_tweet_thread(client, tweet_id):
    """
    指定されたツイートIDから返信のツリーを再帰的に取得する関数
    """
    thread = []
    current_tweet_id = tweet_id
    while current_tweet_id:
        tweet = await client.get_tweet_by_id(str(current_tweet_id))
        if tweet is None:
            break
        thread.insert(0, tweet)  # ツリーの先頭に追加して古いツイートから並ぶようにする
        current_tweet_id = tweet.in_reply_to
    return thread

async def analyze_tweet(client, tweet_id):
    """
    指定されたツイートIDを分析し、リツイートか返信かを判断して
    元のツイート情報を取得するテスト関数
    """
    print("-" * 30)
    print(f"テスト対象ツイートID: {tweet_id}")
    try:
        # ツイートIDを使ってツイートオブジェクトを取得
        tweet = await client.get_tweet_by_id(str(tweet_id))

        if tweet is None:
            print(">>> エラー: ツイートが取得できませんでした (戻り値がNoneです)。")
            return
        # 返信かどうかをチェック
        parent_tweet_id = tweet.in_reply_to
        if parent_tweet_id:
            print("これは返信ツイートです。")
            print(f"返信先のツイートID: {parent_tweet_id}")

            print(">>> 返信ツリーを展開します。")
            thread = await get_tweet_thread(client, tweet_id)
            if thread:
                print(">>> ツイートツリーの取得に成功しました。")
                for i, t in enumerate(thread):
                    print(f"  [{i+1}] 投稿者: @{t.user.screen_name}, 本文: {t.text[:200]}...")
            else:
                print(">>> エラー: ツイートツリーが取得できませんでした。")
            return

        print(">>> このツイートは通常のツイートです（リツイートや返信ではありません）。")

    except Exception as e:
        print(f"処理中に予期せぬエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """
    テストを実行するメイン関数
    """
    print("テストスクリプトを開始します。")
    client = GuestClient()

    print("ゲストトークンを有効化しています...")
    try:
        await client.activate()
        print("ゲストトークンの有効化に成功しました。")
    except Exception as e:
        print(f"\n[エラー] ゲストトークンの有効化に失敗しました: {e}")
        return

    # --- テストケースの実行 ---
    print("\n[ケース1: 返信ツイートの分析]")
    await analyze_tweet(client, REPLY_TWEET_ID)

    print("\n[ケース2: リツイートの分析]")
    await analyze_tweet(client, RETWEET_ID)

    print("\n[ケース3: 通常ツイートの分析]")
    await analyze_tweet(client, PARENT_TWEET_ID)

    print("\n" + "-" * 30)

    print("テストが完了しました。")

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())