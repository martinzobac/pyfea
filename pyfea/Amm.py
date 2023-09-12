import pyfea

""" Virtual meter base class

This file is part of PyFEA.

"""
import pyfea
from typing import *

def floats(string_list) -> List[float]:
    """Convert list of floats represented as strings to list of float numbers."""
    return [float(value) for value in string_list]

def bool_to_str(bool_value):
    if bool_value:
        return "1"
    else:
        return "0"

class Amm(pyfea.Instrument):
    """Base class for all FEA virtual meters."""

    def __init__(self, parent, number, name):
        super().__init__(parent, number, name)

    def select(self):
        self._parent.select_instrument(self.number)

    def get_temperature(self) -> float:
        """Read actual temperature of the virtual instrument.

        Returns
        -------
        float
            Actual internal temperature of the instrument in degrees Celsius
        """
        return float(self._parent.query('DIAG%d:TEMP?' % self.number))

    def measure_current(self) -> float:
        """Measure actual output current.

        Returns
        -------
        float
            Output currents (in amps)
        """
        return float(self._parent.query('MEAS%d:CURR?' % self.number))

    def measure_current_adc(self) -> float:
        """Measure current monitor ADC value.

        Returns
        -------
        float
            Normalized value from current monitor ADC
        """
        return float(self._parent.query('CAL%d:MEAS:CURR:LEVEL?' % self.number))

    def is_ready(self):
        """Check if output channel voltage is ready (settled) or not."""

        self._parent.read_questionable_regs()
        return self.ready

    def _set_ready(self, ready):
        self.ready = ready

    def zero_check(self, enable):
        self._parent.write('SYST:ZCH %s' % bool_to_str(enable))

    def is_zero_check(self):
        return int(self._parent.query('SYST:ZCH?')) != 0

    def auto_zero(self, enable):
        self._parent.write('SYST:ZERO %s' % bool_to_str(enable))

    def is_auto_zero(self):
        return int(self._parent.query('SYST:ZERO?')) != 0

    def set_range(self, range):
        """Set current measurement range

        Parameters
        ----------
        range
            Range in amps
        """
        self._parent.write('MEAS%d:CURR:RANG %f' % (self.number, range))

    def get_range(self) -> float:
        """Get range (in amperes)"""
        return float(self._parent.query('MEAS%d:CURR:RANG?' % self.number))

    def auto_range(self):
        self._parent.write('MEAS%d:CURR:RANG:AUTO' % self.number)

    def is_auto_range(self):
        return int(self._parent.query('MEAS%d:CURR:RANG:AUTO?' % self.number)) != 0

    def set_averaging(self, count):
        self._parent.write('MEAS%d:CURR:AVER %d' % (self.number, count))

    def get_averaging(self):
        return int(self._parent.query('MEAS%d:CURR:RANG:AVER?' % self.number))
