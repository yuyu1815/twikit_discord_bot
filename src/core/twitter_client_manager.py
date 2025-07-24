import asyncio
from pathlib import Path
from typing import Optional, Union

from twikit import Client
from twikit.guest import GuestClient
from twikit.errors import TooManyRequests, Unauthorized

class TwitterClientManager:
    """
    Manages Twitter API clients (both guest and authenticated) and provides
    appropriate clients based on the operation type.
    Twitter API クライアント（ゲストおよび認証済み）を管理し、操作タイプに基づいて適切なクライアントを提供します。
    """

    def __init__(self, settings=None, cookie_path=None):
        """
        Initialize the Twitter client manager.
        Twitter クライアントマネージャーを初期化します。

        Args:
            settings (Settings, optional): Settings object for language support
            settings (Settings, optional): 言語サポートのための設定オブジェクト
            cookie_path (str, optional): Path to the cookie file
            cookie_path (str, optional): クッキーファイルへのパス
        """
        self.settings = settings
        self.cookie_path = cookie_path or Path(__file__).parent.parent.parent / 'data' / 'cookie_edit.json'

        # Initialize clients
        self.guest_client = GuestClient()
        self.auth_client = Client('en-US')

        # Client state tracking
        self.guest_client_active = False
        self.auth_client_active = False

        # Rate limit tracking
        self.guest_rate_limited = False
        self.auth_rate_limited = False

        # Rate limit reset times
        self.guest_rate_limit_reset = 0
        self.auth_rate_limit_reset = 0

    async def initialize(self):
        """
        Initialize and activate both guest and authenticated Twitter clients.
        This method attempts to activate both clients to ensure maximum availability
        for Twitter API interactions.

        ゲストおよび認証済みTwitterクライアントの両方を初期化し、アクティブ化します。
        このメソッドは、Twitter APIとの対話で最大限の可用性を確保するために、両方のクライアントをアクティブ化しようとします。

        Returns:
            bool: True if at least one client was successfully activated, False otherwise.
                  少なくとも1つのクライアントが正常にアクティブ化された場合はTrue、それ以外の場合はFalse。
        """
        guest_success = await self._activate_guest_client()
        auth_success = await self._activate_auth_client()

        return guest_success or auth_success

    async def _activate_guest_client(self):
        """
        Activate the guest client.
        The guest client does not require authentication and is used for basic data fetching.

        ゲストクライアントをアクティブ化します。
        ゲストクライアントは認証を必要とせず、基本的なデータ取得に使用されます。

        Returns:
            bool: True if activation was successful, False otherwise.
                  アクティブ化が成功した場合はTrue、それ以外の場合はFalse。
        """
        try:
            await self.guest_client.activate()
            self.guest_client_active = True
            self.guest_rate_limited = False
            return True
        except Exception as e:
            # Log the error if guest client activation fails.
            # ゲストクライアントのアクティブ化に失敗した場合、エラーをログに記録します。
            if self.settings:
                print(self.settings.lang_data.get("twitter_guest_activation_failed", "Guest client activation failed: {}").format(str(e)))
            else:
                print(f"Guest client activation failed: {str(e)}")
            self.guest_client_active = False
            return False

    async def _activate_auth_client(self):
        """
        Activate the authenticated client by loading cookies.
        The authenticated client is used for operations requiring user authentication, such as fetching user timelines.

        クッキーをロードして認証済みクライアントをアクティブ化します。
        認証済みクライアントは、ユーザーのタイムラインの取得など、ユーザー認証を必要とする操作に使用されます。

        Returns:
            bool: True if activation was successful, False otherwise.
                  アクティブ化が成功した場合はTrue、それ以外の場合はFalse。
        """
        try:
            cookie_file = Path(self.cookie_path)
            if not cookie_file.exists():
                # If cookie file is not found, print a warning and mark client as inactive.
                # クッキーファイルが見つからない場合、警告を出力し、クライアントを非アクティブとしてマークします。
                if self.settings:
                    print(self.settings.lang_data.get("twitter_cookie_not_found", "Cookie file not found: {}").format(self.cookie_path))
                else:
                    print(f"Cookie file not found: {self.cookie_path}")
                self.auth_client_active = False
                return False

            self.auth_client.load_cookies(str(cookie_file))
            self.auth_client_active = True
            self.auth_rate_limited = False
            return True
        except Exception as e:
            # Log the error if authenticated client activation fails.
            # 認証済みクライアントのアクティブ化に失敗した場合、エラーをログに記録します。
            if self.settings:
                print(self.settings.lang_data.get("twitter_auth_activation_failed", "Authenticated client activation failed: {}").format(str(e)))
            else:
                print(f"Authenticated client activation failed: {str(e)}")
            self.auth_client_active = False
            return False

    async def get_analysis_client(self):
        """
        Get a client suitable for tweet analysis operations (e.g., checking if a tweet is a retweet).
        Prioritizes the guest client if it's active and not rate-limited.
        Falls back to the authenticated client if the guest client is unavailable or rate-limited.

        ツイート分析操作（例: ツイートがリツイートであるかどうかの確認）に適したクライアントを取得します。
        ゲストクライアントがアクティブでレート制限されていない場合、ゲストクライアントを優先します。
        ゲストクライアントが利用できないかレート制限されている場合、認証済みクライアントにフォールバックします。

        Returns:
            Union[GuestClient, Client]: The appropriate client for analysis operations.
                                       分析操作に適したクライアント。

        Raises:
            RuntimeError: If no clients are available for analysis operations.
                          分析操作に利用できるクライアントがない場合。
        """
        # Check if guest client is available and not rate limited.
        # ゲストクライアントが利用可能でレート制限されていないかを確認します。
        if self.guest_client_active and not self.guest_rate_limited:
            return self.guest_client

        # Fall back to authenticated client if available and not rate limited.
        # 利用可能でレート制限されていない場合、認証済みクライアントにフォールバックします。
        if self.auth_client_active and not self.auth_rate_limited:
            return self.auth_client

        # If guest client is rate limited but auth client is not available, try to use guest client anyway.
        # ゲストクライアントがレート制限されているが認証済みクライアントが利用できない場合、とにかくゲストクライアントを使用しようとします。
        if self.guest_client_active:
            return self.guest_client

        # If auth client is rate limited but guest client is not available, try to use auth client anyway.
        # 認証済みクライアントがレート制限されているがゲストクライアントが利用できない場合、とにかく認証済みクライアントを使用しようとします。
        if self.auth_client_active:
            return self.auth_client

        # If no clients are active or available, raise an error.
        # クライアントがアクティブでないか利用できない場合、エラーを発生させます。
        raise RuntimeError("No Twitter clients are available for analysis operations")

    async def get_authenticated_client(self):
        """
        Get an authenticated client for operations that require authentication
        (e.g., fetching user timelines for new tweets).

        認証を必要とする操作（例: 新しいツイートのユーザータイムラインの取得）のための
        認証済みクライアントを取得します。

        Returns:
            Client: The authenticated client.
                    認証済みクライアント。

        Raises:
            RuntimeError: If the authenticated client is not available.
                          認証済みクライアントが利用できない場合。
        """
        if not self.auth_client_active:
            raise RuntimeError("Authenticated Twitter client is not available for timeline operations")

        return self.auth_client

    async def handle_rate_limit(self, client_type, reset_time=None):
        """
        Mark a specific client type as rate-limited and record the reset time.
        This prevents further attempts to use the rate-limited client until the reset time has passed.

        特定のクライアントタイプをレート制限としてマークし、リセット時間を記録します。
        これにより、リセット時間が経過するまで、レート制限されたクライアントの使用をさらに試みることを防ぎます。

        Args:
            client_type (str): The type of client to mark as rate-limited ('guest' or 'auth').
                               レート制限としてマークするクライアントのタイプ（'guest'または'auth'）。
            reset_time (int, optional): The Unix timestamp when the rate limit is expected to reset.
                                        If None, defaults to 15 minutes from now.
                                        レート制限がリセットされると予想されるUnixタイムスタンプ。
                                        Noneの場合、現在から15分後にデフォルト設定されます。
        """
        if client_type == 'guest':
            self.guest_rate_limited = True
            # Set reset time, defaulting to 15 minutes if not provided.
            # リセット時間を設定します。提供されない場合は15分にデフォルト設定されます。
            self.guest_rate_limit_reset = reset_time or (asyncio.get_event_loop().time() + 900)  # Default 15 minutes
        elif client_type == 'auth':
            self.auth_rate_limited = True
            # Set reset time, defaulting to 15 minutes if not provided.
            # リセット時間を設定します。提供されない場合は15分にデフォルト設定されます。
            self.auth_rate_limit_reset = reset_time or (asyncio.get_event_loop().time() + 900)  # Default 15 minutes

    async def execute_with_fallback(self, operation, *args, **kwargs):
        """
        Execute a given asynchronous operation, with automatic fallback to another client
        if the primary client encounters a TooManyRequests (rate limit) or Unauthorized error.

        指定された非同期操作を実行します。プライマリクライアントがTooManyRequests（レート制限）
        またはUnauthorizedエラーに遭遇した場合、自動的に別のクライアントにフォールバックします。

        Args:
            operation (callable): The asynchronous function to execute (e.g., client.get_tweet_by_id).
                                  実行する非同期関数（例: client.get_tweet_by_id）。
            *args: Positional arguments to pass to the operation.
                   操作に渡す位置引数。
            **kwargs: Keyword arguments to pass to the operation.
                      操作に渡すキーワード引数。

        Returns:
            Any: The result of the successful operation.
                 成功した操作の結果。

        Raises:
            Exception: If the operation fails with both clients or an unhandled error occurs.
                       両方のクライアントで操作が失敗した場合、または未処理のエラーが発生した場合。
        """
        try:
            # Attempt to execute the operation using the analysis client (which prioritizes guest).
            # 分析クライアント（ゲストを優先）を使用して操作を実行しようとします。
            client = await self.get_analysis_client()
            return await operation(client, *args, **kwargs)
        except TooManyRequests as e:
            # If a TooManyRequests error occurs, handle the rate limit for the current client.
            # TooManyRequestsエラーが発生した場合、現在のクライアントのレート制限を処理します。
            if isinstance(client, GuestClient):
                # If the guest client is rate-limited, mark it and try with the authenticated client.
                # ゲストクライアントがレート制限された場合、それをマークし、認証済みクライアントで試行します。
                await self.handle_rate_limit('guest', getattr(e, 'rate_limit_reset', None))
                if self.auth_client_active:
                    try:
                        # Attempt with the authenticated client.
                        # 認証済みクライアントで試行します。
                        return await operation(self.auth_client, *args, **kwargs)
                    except TooManyRequests as e2:
                        # If authenticated client also gets rate-limited, mark it and re-raise the exception.
                        # 認証済みクライアントもレート制限された場合、それをマークして例外を再発生させます。
                        await self.handle_rate_limit('auth', getattr(e2, 'rate_limit_reset', None))
                        raise
            else:
                # If the authenticated client is rate-limited, mark it and re-raise the exception.
                # 認証済みクライアントがレート制限された場合、それをマークして例外を再発生させます。
                await self.handle_rate_limit('auth', getattr(e, 'rate_limit_reset', None))
                raise
        except Unauthorized:
            # If an Unauthorized error occurs (e.g., guest client token expired), try with the authenticated client.
            # Unauthorizedエラーが発生した場合（例: ゲストクライアントのトークン期限切れ）、認証済みクライアントで試行します。
            if isinstance(client, GuestClient) and self.auth_client_active:
                return await operation(self.auth_client, *args, **kwargs)
            raise
        except Exception as e:
            # For any other unexpected exceptions, if the guest client was used, try with the authenticated client.
            # その他の予期せぬ例外の場合、ゲストクライアントが使用された場合は認証済みクライアントで試行します。
            if isinstance(client, GuestClient) and self.auth_client_active:
                try:
                    return await operation(self.auth_client, *args, **kwargs)
                except Exception:
                    # If both clients fail, re-raise the original exception.
                    # 両方のクライアントが失敗した場合、元の例外を再発生させます。
                    raise e
            raise
