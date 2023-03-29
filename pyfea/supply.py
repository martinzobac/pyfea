"""Virtual power supply base class

This file is part of PyFEA.

"""
import pyfea
from typing import (List)


def floats(string_list) -> List[float]:
    """Convert list of floats represented as strings to list of float numbers."""
    return [float(value) for value in string_list]

def bool_to_str(bool_value):
    if bool_value:
        return "1"
    else:
        return "0"

class Supply(pyfea.Instrument):
    """Base class for all FEA virtual power supplies."""

    def __init__(self, parent, number, name):
        super().__init__(parent, number, name)
        self.max_voltage = 0
        self.min_voltage = 0
        self.voltage = 0

    def select(self):
        self._parent.select_instrument(self.number)

    def turn_on(self, wait=True):
        """Turn on the virtual instrument.

        Parameters
        ----------
        wait
            When True the method will wait for operation completed signal.
        """
        self._parent.write('INST%d:STAT ON' % self.number)
        if wait:
            self._parent.wait_for_operation_complete()

    def turn_off(self, wait=True):
        """Turn off the virtual instrument.

        Parameters
        ----------
        wait
            When True the method will wait for operation completed signal.
        """
        self._parent.write('INST%d:STAT OFF' % self.number)
        if wait:
            self._parent.wait_for_operation_complete()

    def get_state(self):
        """Read if instrument is turned on or not."""
        return int(self._parent.query('INST%d:STAT?' % self.number)) != 0

    def get_temperature(self) -> float:
        """Read actual temperature of the virtual instrument.

        Returns
        -------
        float
            Actual internal temperature of the instrument in degrees Celsius
        """
        return float(self._parent.query('DIAG%d:TEMP?' % self.number))

    def set_voltage(self, voltage):
        """Set output voltage."""
        self._parent.write('SOUR%d:VOLT %f' % (self.number, voltage))

    def get_voltage(self) -> float:
        return float(self._parent.query('SOUR%d:VOLT?' % (self.number)))

    def set_range(self, range, range2=None):
        self._parent.write('OUTP%d:RANG %f' % (self.number, range) +
                           ', %f' % range2 if range2 else '')

    def get_range(self):
        return floats(self._parent.query('OUTP%d:RANG?' % self.number))

    def measure_voltage(self) -> float:
        """Measure actual output voltage.

        Returns
        -------
        float
            Output voltage (in volts)
        """
        return float(self._parent.query('MEAS%d:VOLT?' % self.number))

    def measure_current(self) -> float:
        """Measure actual output current.

        Returns
        -------
        float
            Output currents (in amps)
        """
        return float(self._parent.query('MEAS%d:CURR?' % self.number))

    def measure_voltage_adc(self) -> float:
        """Measure voltage monitor ADC value.

        Returns
        -------
        float
            Normalized value from voltage monitor ADC
        """
        return float(self._parent.query('CAL%d:MEAS:VOLT:LEVEL?' % self.number))

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

    def set_calibration_output_range(self, low, high):
        """Set output hardware limits."""
        self._parent.write('CAL%d:OUTP:RANGE %f,%f' % (self.number, low, high))

    def set_range(self, range, range2=None):
        if not range2:
            if range > 0:
                range = -range
            range2 = -range

        self._parent.write('OUTP%d:RANG %f' % (self.number, range) +
                           ', %f' % range2 if range2 else '')

    def set_vmonit_calibration_points(self, points):
        """Set voltage monitor calibration points."""
        self._set_calibration_points(points,'MEAS:VOLT')

    def set_imonit_calibration_points(self, points):
        """Set current monitor calibration points."""
        self._set_calibration_points(points,'MEAS:CURR')

    def set_program_calibration_points(self, points):
        """Set voltage program calibration points."""
        self._set_calibration_points(points,'SOUR:VOLT')

    def get_program_calibration_points(self):
        """Get voltage program calibration points."""
        return self._get_calibration_points('SOUR:VOLT')

    def set_quiscent_compensation_points(self, points):
        """Set quiescent current compensation points."""
        self._set_calibration_points(points,'MEAS:CURR:QCOM')

    def _set_calibration_points(self, points, target):
        self._parent.write('CAL%d:%s:COUNT 0' % (self.number, target))

        if len(points) > 0:
            value_list = [val for tup in points for val in tup]
            value_string = ','.join(map(str, value_list))

            self._parent.write('CAL%d:%s:DATA 0,%s' % (self.number, target, value_string))
            self._parent.write('CAL%d:%s:COUNT %d' % (self.number, target, len(points)))

    def _get_calibration_points(self, target):
        response = self._parent.query('CAL%d:%s:CAT?' % (self.number, target))
        values = floats(response.split(','))
        return [(values[i], values[i+1]) for i in range(0, len(values), 2)]

    def quiescent_compensation(self, enable):
        self._parent.write('CAL%d:MEAS:CURR:QCOM:STATE %s' % (self.number, bool_to_str(enable)))

