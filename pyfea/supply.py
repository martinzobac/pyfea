"""Virtual power supply base class

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
        self._parent.write('OUTP%d:STAT ON' % self.number)
        if wait:
            self._parent.wait_for_operation_complete()

    def turn_off(self, wait=True):
        """Turn off the virtual instrument.

        Parameters
        ----------
        wait
            When True the method will wait for operation completed signal.
        """
        self._parent.write('OUTP%d:STAT OFF' % self.number)
        if wait:
            self._parent.wait_for_operation_complete()

    def get_state(self):
        """Read if instrument is turned on or not."""
        return int(self._parent.query('OUTP%d:STAT?' % self.number)) != 0

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

    def set_ocp(self, enable):
        self._parent.write('OUTP%d:OCP:STAT %s' % (self.number, bool_to_str(enable)))

    def get_ocp(self):
        return bool(self._parent.query('OUTP%d:OCP:STAT?' % self.number))

    def set_ovp(self, enable):
        self._parent.write('OUTP%d:OVP:STAT %s' % (self.number, bool_to_str(enable)))

    def get_ovp(self):
        return bool(self._parent.query('OUTP%d:OVP:STAT?' % self.number))

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

    def set_calibration_output_range(self, hw_range):
        """Set output hardware limits.
        Used during commissioning only.

        Parameters
        ----------
        hw_range
            Maximum permitted output voltage (hardware limit) in volts.
        """
        self._parent.write('CAL%d:OUTP:RANGE %f' % (self.number, hw_range))

    def set_range(self, output_range):
        """Set output soft voltage limit

        Parameters
        ----------
        output_range
            User defined maximum output voltage in volts.
        """
        self._parent.write('OUTP%d:RANG %f' % (self.number, output_range))

    def get_range(self) -> float:
        """Get output soft voltage limit (in volts)"""
        return float(self._parent.query('OUTP%d:RANG?' % self.number))

    def set_rise_rate(self, rise_rate):
        """Set output rise rate (in volts per second)

        Parameters
        ----------
        rise_rate
            Desired rate of change of rising output voltage in volts per second.
        """
        self._parent.write('OUTP%d:RISE %f' % (self.number, rise_rate))

    def get_rise_rate(self) -> float:
        """Get output rise rate (in volts per second)"""
        return float(self._parent.query('OUTP%d:RISE?' % self.number))

    def set_fall_rate(self, fall_rate):
        """Set output fall rate (in volts per second)

        Parameters
        ----------
        fall_rate
            Desired rate of change of falling output voltage in volts per second.
        """
        self._parent.write('OUTP%d:FALL %f' % (self.number, fall_rate))

    def get_fall_rate(self) -> float:
        """Get output fall rate (in volts per second)"""
        return float(self._parent.query('OUTP%d:FALL?' % self.number))

    def set_vmonit_calibration_points(self, points):
        """Set voltage monitor calibration points.

        Parameters
        ----------
        points
            List of pair tuples.
            Each pair is one point of piece-wise conversion curve.
            The first value of tuple pair is voltage monitor normalize ADC value.
            The second value of tuple pair is actual output voltage in volts.
        """
        self._set_calibration_points(points,'MEAS:VOLT')

    def set_imonit_calibration_points(self, points):
        """Set current monitor calibration points.

        Parameters
        ----------
        points
            List of pair tuples.
            Each pair is one point of piece-wise conversion curve.
            The first value of tuple pair is current monitor normalize ADC value.
            The second value of tuple pair is actual output current in amps.
        """
        self._set_calibration_points(points,'MEAS:CURR')

    def set_program_calibration_points(self, points):
        """Set voltage program calibration points.

        Parameters
        ----------
        points
            List of pair tuples.
            Each pair is one point of piece-wise conversion curve.
            The first value of tuple pair is output voltage in volts.
            The second value of tuple pair is normalized DAC value of voltage program.
        """

        self._set_calibration_points(points,'SOUR:VOLT')

    def get_program_calibration_points(self) -> List[Tuple[float, float]]:
        """Get voltage program calibration points."""
        return self._get_calibration_points('SOUR:VOLT')

    def set_quiescent_compensation_points(self, points):
        """Set quiescent current compensation points.

        Parameters
        ----------
        points
            List of pair tuples.
            Each pair is one point of piece-wise conversion curve.
            The first value of tuple pair is normalized ADC value of voltage monitor.
            The second value of tuple pair is normalized ADC value of current monitor measured without output load.
        """
        self._set_calibration_points(points,'MEAS:CURR:QCOM')

    def quiescent_compensation(self, enable):
        """Enable or disable quiescent current compensation

        Parameters
        ----------
        enable
            When True enable quiescent current compensation
        """
        self._parent.write('CAL%d:MEAS:CURR:QCOM:STATE %s' % (self.number, bool_to_str(enable)))

    def _set_calibration_points(self, points, target):
        self._parent.write('CAL%d:%s:COUNT 0' % (self.number, target))

        if len(points) > 0:
            value_list = [val for tup in points for val in tup]
            value_string = ','.join([f"{num:.6g}" for num in value_list])

            self._parent.write('CAL%d:%s:DATA 0,%s' % (self.number, target, value_string))
            self._parent.write('CAL%d:%s:COUNT %d' % (self.number, target, len(points)))

    def _get_calibration_points(self, target) -> List[Tuple[float, float]]:
        response = self._parent.query('CAL%d:%s:CAT?' % (self.number, target))
        values = floats(response.split(','))
        return [(values[i], values[i+1]) for i in range(0, len(values), 2)]


