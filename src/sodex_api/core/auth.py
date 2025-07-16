"""Authentication module for Sodex API."""

import hashlib
import hmac
import time
import uuid
from typing import Dict, Any


class Authenticator:
    """Handles authentication for Sodex API requests."""
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
    
    def generate_signature(self, params: Dict[str, Any], timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for authenticated requests.
        
        Args:
            params: Request parameters
            timestamp: Request timestamp
            
        Returns:
            Generated signature
        """
        # Sort parameters by key
        sorted_params = dict(sorted(params.items()))
        
        # Build raw string from parameters
        raw_string = "&".join([f"{key}={value}" for key, value in sorted_params.items()])
        
        # Add timestamp parameter
        raw_string += f"&timestamp={timestamp}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def get_auth_headers(self, params: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Get authentication headers for a request.
        
        Args:
            params: Request parameters
            
        Returns:
            Dict containing authentication headers
        """
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())
        
        headers = {
            'X-Access-Key': self.api_key,
            'X-Request-Timestamp': timestamp,
            'X-Request-Nonce': nonce,
        }
        
        if params is not None:
            headers['X-Signature'] = self.generate_signature(params, timestamp)
        
        return headers