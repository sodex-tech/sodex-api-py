"""Base classes for Sodex API clients."""

import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from .auth import Authenticator
from .exceptions import (
    SodexAPIError,
    AuthenticationError,
    RateLimitError,
    NetworkError
)


class BaseClient(ABC):
    """Base class for REST API clients."""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str, timeout: float = 10.0):
        self.authenticator = Authenticator(api_key, secret_key)
        self.base_url = base_url
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create and configure requests session."""
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SodexTradingBot/2.0'
        })
        return session
    
    def _handle_response(self, response_data: Dict[str, Any]) -> Any:
        """
        Handle and validate API response.
        
        Args:
            response_data: Raw response data
            
        Returns:
            Response data or None
            
        Raises:
            SodexAPIError: If response indicates error
        """
        code = response_data.get('code', -1)
        
        if code != 0:
            error_msg = response_data.get('msg', 'Unknown error')
            
            # Map error codes to specific exceptions
            if 1001 <= code <= 1013:  # Authentication errors
                raise AuthenticationError(f"API Error: {error_msg}", code, response_data)
            elif code == 429:  # Rate limit
                raise RateLimitError(f"API Error: {error_msg}", code, response_data)
            else:
                raise SodexAPIError(f"API Error: {error_msg}", code, response_data)
        
        return response_data.get('data')
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     params: Optional[Dict[str, Any]] = None, 
                     signed: bool = False) -> Any:
        """
        Make HTTP request to Sodex API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request requires authentication
            
        Returns:
            Response data
            
        Raises:
            SodexAPIError: If request fails
        """
        if params is None:
            params = {}
        
        headers = self.session.headers.copy()
        
        if signed:
            # Add authentication headers
            auth_headers = self.authenticator.get_auth_headers(params)
            headers.update(auth_headers)
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return self._handle_response(response.json())
        
        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timeout for {endpoint}")
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {response.status_code} for {endpoint}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg += f": {error_data.get('msg', 'Unknown error')}"
                except (ValueError, KeyError):
                    error_msg += f": {e.response.text}"
            raise NetworkError(error_msg)
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error for {endpoint}: {str(e)}")


class BaseWebSocketClient(ABC):
    """Base class for WebSocket clients."""
    
    def __init__(self, api_key: str, secret_key: str, ws_url: str):
        self.authenticator = Authenticator(api_key, secret_key)
        self.ws_url = ws_url
        self.ws = None
        self.is_connected = False
    
    @abstractmethod
    async def connect(self):
        """Connect to WebSocket server."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        pass
    
    @abstractmethod
    async def subscribe(self, channel: str, params: Dict[str, Any] = None):
        """Subscribe to a channel."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, channel: str, params: Dict[str, Any] = None):
        """Unsubscribe from a channel."""
        pass