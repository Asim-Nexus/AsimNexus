"""AsimNexus Kernel module."""

# Re-export from root-level module: event_bus.py
from core.event_bus import (
    ASIMEvent,
    ASIMEventBus,
    AllocationPriority,
    EventType,
    event_bus,
)


# Re-export from root-level module: platform.py
from core.platform import (
    PlatformManager,
    get_platform_manager,
)

