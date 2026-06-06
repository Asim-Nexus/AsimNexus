
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Nepal Digital Dharma Framework
================================
Ancient Indian/Nepali wisdom integrated into modern computing

This framework integrates principles from:
- Pingala (binary/combinatorial optimization)
- Shulba (geometric algorithms)
- Panini (grammar parsing)
- Nyaya (logic reasoning)
- Upanishads (ethics)
- Tantra/Mantra/Yantra (pattern-based automation)

For all countries with their own cultural/dharma frameworks.
"""

from .nepal_digital_dharma import NepalDigitalDharma, get_nepal_dharma
from .pingala import PingalaLayer
from .shulba import ShulbaLayer
from .panini import PaniniLayer
from .nyaya import NyayaLayer
from .upanishad import UpanishadLayer
from .tantra import TantraLayer
from .country_dharma import CountryDharmaManager
from .delta_t_production import DeltaTProduction, get_delta_t_production
from .delta_t_integration import DeltaTIntegration, get_delta_t_integration
from .delta_t_mesh import DeltaTMeshIntegration, get_delta_t_mesh

__version__ = "1.0.0"
__all__ = [
    "NepalDigitalDharma",
    "get_nepal_dharma",
    "PingalaLayer",
    "ShulbaLayer",
    "PaniniLayer",
    "NyayaLayer",
    "UpanishadLayer",
    "TantraLayer",
    "CountryDharmaManager",
    "DeltaTProduction",
    "get_delta_t_production",
    "DeltaTIntegration",
    "get_delta_t_integration",
    "DeltaTMeshIntegration",
    "get_delta_t_mesh"
]
