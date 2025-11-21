# src/interfaces/__init__.py
from .i_source import ITaskSource
from .i_device import IDevice
from .i_buffer import IBuffer

__all__ = ["ITaskSource", "IDevice", "IBuffer"]