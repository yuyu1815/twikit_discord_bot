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
        Initialize and activate both clients.

        Returns:
            bool: True if at least one client was successfully activated
        """
        guest_success = await self._activate_guest_client()
        auth_success = await self._activate_auth_client()

        return guest_success or auth_success

    async def _activate_guest_client(self):
        """
        Activate the guest client.

        Returns:
            bool: True if activation was successful, False otherwise
        """
        try:
            await self.guest_client.activate()
            self.guest_client_active = True
            self.guest_rate_limited = False
            return True
        except Exception as e:
            if self.settings:
                print(self.settings.lang_data.get("twitter_guest_activation_failed", "Guest client activation failed: {}").format(str(e)))
            else:
                print(f"Guest client activation failed: {str(e)}")
            self.guest_client_active = False
            return False

    async def _activate_auth_client(self):
        """
        Activate the authenticated client by loading cookies.

        Returns:
            bool: True if activation was successful, False otherwise
        """
        try:
            cookie_file = Path(self.cookie_path)
            if not cookie_file.exists():
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
            if self.settings:
                print(self.settings.lang_data.get("twitter_auth_activation_failed", "Authenticated client activation failed: {}").format(str(e)))
            else:
                print(f"Authenticated client activation failed: {str(e)}")
            self.auth_client_active = False
            return False

    async def get_analysis_client(self):
        """
        Get a client for tweet analysis operations.
        Prioritizes the guest client, falling back to the authenticated client if necessary.

        Returns:
            Union[GuestClient, Client]: The appropriate client for analysis

        Raises:
            RuntimeError: If no clients are available
        """
        # Check if guest client is available and not rate limited
        if self.guest_client_active and not self.guest_rate_limited:
            return self.guest_client

        # Fall back to authenticated client if available
        if self.auth_client_active and not self.auth_rate_limited:
            return self.auth_client

        # If guest client is rate limited but auth client is not available, try to use guest client anyway
        if self.guest_client_active:
            return self.guest_client

        # If auth client is rate limited but guest client is not available, try to use auth client anyway
        if self.auth_client_active:
            return self.auth_client

        # No clients available
        raise RuntimeError("No Twitter clients are available for analysis operations")

    async def get_rss_client(self):
        """
        Get a client for RSS-like operations (timeline fetching, etc.).
        Always uses the authenticated client.

        Returns:
            Client: The authenticated client

        Raises:
            RuntimeError: If the authenticated client is not available
        """
        if not self.auth_client_active:
            raise RuntimeError("Authenticated Twitter client is not available for RSS operations")

        return self.auth_client

    async def handle_rate_limit(self, client_type, reset_time=None):
        """
        Handle rate limit for a specific client type.

        Args:
            client_type (str): Either 'guest' or 'auth'
            reset_time (int, optional): The time when the rate limit resets (Unix timestamp)
        """
        if client_type == 'guest':
            self.guest_rate_limited = True
            self.guest_rate_limit_reset = reset_time or (asyncio.get_event_loop().time() + 900)  # Default 15 minutes
        elif client_type == 'auth':
            self.auth_rate_limited = True
            self.auth_rate_limit_reset = reset_time or (asyncio.get_event_loop().time() + 900)  # Default 15 minutes

    async def execute_with_fallback(self, operation, *args, **kwargs):
        """
        Execute an operation with automatic client fallback if rate limited.

        Args:
            operation (callable): The operation to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            Any: The result of the operation

        Raises:
            Exception: If the operation fails with both clients
        """
        try:
            # Try with analysis client first (prioritizes guest)
            client = await self.get_analysis_client()
            return await operation(client, *args, **kwargs)
        except TooManyRequests as e:
            # Handle rate limit
            if isinstance(client, GuestClient):
                await self.handle_rate_limit('guest', getattr(e, 'rate_limit_reset', None))
                # Try with authenticated client
                if self.auth_client_active:
                    try:
                        return await operation(self.auth_client, *args, **kwargs)
                    except TooManyRequests as e2:
                        await self.handle_rate_limit('auth', getattr(e2, 'rate_limit_reset', None))
                        raise
            else:
                await self.handle_rate_limit('auth', getattr(e, 'rate_limit_reset', None))
                raise
        except Unauthorized:
            # If guest client authentication fails, try with authenticated client
            if isinstance(client, GuestClient) and self.auth_client_active:
                return await operation(self.auth_client, *args, **kwargs)
            raise
        except Exception as e:
            # For other exceptions, if using guest client, try with authenticated client
            if isinstance(client, GuestClient) and self.auth_client_active:
                try:
                    return await operation(self.auth_client, *args, **kwargs)
                except Exception:
                    # If both fail, raise the original exception
                    raise e
            raise
