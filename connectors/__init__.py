
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Connectors Module - External API Integration
"""

from .government_api import GovernmentAPIConnector
from .health_api import HealthAPIConnector
from .education_api import EducationAPIConnector
from .deepseek_connector import DeepSeekConnector
from .news_connector import NewsConnector
from .crypto_connector import CryptoConnector
from .cloudinary_connector import CloudinaryConnector
from .supabase_connector import SupabaseConnector
from .pollinations_connector import PollinationsConnector
from .mongodb_connector import MongoDBConnector

# New 2026 Components
from .unified_messaging_connector import UnifiedMessagingConnector, messaging_connector
from .smart_model_router import SmartModelRouter, model_router

__all__ = [
    'GovernmentAPIConnector',
    'HealthAPIConnector',
    'EducationAPIConnector',
    'DeepSeekConnector',
    'NewsConnector',
    'CryptoConnector',
    'CloudinaryConnector',
    'SupabaseConnector',
    'PollinationsConnector',
    'MongoDBConnector',
    # New exports
    'UnifiedMessagingConnector',
    'messaging_connector',
    'SmartModelRouter',
    'model_router'
]
