"""The Jamesian Layer: autonomic interoceptive middleware for foundation models."""

__version__ = "0.1.0"

from jamesian_layer.config import Settings
from jamesian_layer.core.biophysical_state import BiophysicalState

__all__ = ["Settings", "BiophysicalState", "__version__"]
