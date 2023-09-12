"""Virtual instrument base class

This file is part of PyFEA.

"""
from typing import (List)


def floats(string_list) -> List[float]:
    """Convert list of floats represented as strings to list of float numbers."""
    return [float(value) for value in string_list]


def bools(string_list) -> List[bool]:
    """Convert list of floats represented as strings to list of float numbers."""
    return [int(value) != 0 for value in string_list]






class Instrument:
    """Base class for all FEA virtual instruments."""

    def __init__(self, parent, number, name):
        self._parent = parent
        self.number = number
        self.name = name
        self.ready = False
        self.type = "Unknown"

    def select(self):
        self._parent.select_instrument(self.number)

    def is_ready(self, channel):
        """Check if is ready or not."""

        self._parent.read_questionable_regs()

        if channel not in self.channels:
            return None
        else:
            return self.ready[channel - 1]

    def _set_ready(self, channel, ready):
        if channel in self.channels:
            self.ready[channel - 1] = ready

