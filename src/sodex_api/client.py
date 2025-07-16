"""Legacy client module for backward compatibility."""

from .spot.client import SpotClient

# Create alias for backward compatibility
SodexClient = SpotClient