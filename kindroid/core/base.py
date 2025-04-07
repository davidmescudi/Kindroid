"""
Base classes and interfaces for Kindroid hardware modules.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class HardwareModule(ABC):
    """Base class for all hardware modules."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the hardware module."""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown the hardware module."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the module."""
        pass 