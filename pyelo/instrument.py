"""Virtual instrument base class

This file is part of PyELO.

"""
from pyelo.errors import *
from typing import (List)
from datetime import datetime


def floats(string_list) -> List[float]:
    """Convert list of floats represented as strings to list of float numbers."""
    return [float(value) for value in string_list]


def bools(string_list) -> List[bool]:
    """Convert list of floats represented as strings to list of float numbers."""
    return [int(value) != 0 for value in string_list]


def bool_to_str(bool_value):
    if bool_value:
        return "1"
    else:
        return "0"


def str_to_bool(string):
    if (string=='0') | (string=='OFF'):
        return False
    elif (string=='1') | (string=='ON'):
        return True
    else:
        raise ExpectedBooleanValue(string)


class Instrument:
    """Base class for all ELO virtual instruments."""

    def __init__(self, parent, number, name):
        self._parent = parent
        self.number = number
        self.name = name
        self.channels = ()
        self.ready = []
        self.max_voltage = 0
        self.min_voltage = 0
        self.voltages = []
        self.type = "Unknown"

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

    def _channel_list(self, channels):
        if not channels:
            channels = self.channels

        if not isinstance(channels, tuple) and not isinstance(channels, list):
            channels = [channels, ]

        return [int(channel) for channel in channels]

    def _channel_str_list(self, channels) -> str:
        """Convert channel tuple or list to comma separated list.

        Parameters
        ----------
        channels
            Tuple or list of channel numbers.

        Returns
        -------
        str
            Comma separated list of channel numbers
        """
        channels = self._channel_list(channels)
        string = ''
        for channel in channels:
            if channel not in self.channels:
                raise WrongChannel(self, channel)
            else:
                if string != '':
                    string += ','
                string += str(channel)
        return string

    def turn_on_channels(self, channels=None):
        """Turn on one or more channels."""
        self._parent.write('OUTP%d:STAT (@%s),ON' % (self.number, self._channel_str_list(channels)))

    def turn_off_channels(self, channels=None):
        """Turn off one or more channels."""
        self._parent.write('OUTP%d:STAT (@%s),OFF' % (self.number, self._channel_str_list(channels)))

    def get_channels_state(self, channels=None):
        response = self._parent.query('OUTP%d:STAT? (@%s)' % (self.number, self._channel_str_list(channels))).split(',')
        return bools(response)

    def set_voltage(self, channels, voltages):
        """Set one or more channels' voltages."""
        if not isinstance(voltages, list) and not isinstance(voltages, tuple):
            voltages = [voltages]

        channels = self._channel_list(channels)

        for channel, voltage in zip(channels, voltages):
            self.voltages[int(channel-1)] = voltage

        voltages = [str(v) for v in voltages]
        self._parent.write('SOUR%d:VOLT (@%s),%s' % (self.number, self._channel_str_list(channels), ','.join(voltages)))

    def get_voltage(self, channels=None) -> List[float]:
        return floats(self._parent.query('SOUR%d:VOLT? (@%s)' %
                                         (self.number, self._channel_str_list(channels))).split(','))
        #channels = self._channel_list(channels)
        #voltages = []
        #for channel in channels:
        #    voltages.append(self.voltages[channel-1])
        #return voltages

    def set_range(self, channels, range, range2=None):
        channels = self._channel_list(channels)
        self._parent.write('OUTP%d:RANG (@%s),%f' % (self.number, self._channel_str_list(channels), range) +
                           ', %f' % range2 if range2 else '')

    def get_range(self, channel=1):
        return floats(self._parent.query('OUTP%d:RANG? (@%d)' % (self.number, channel)).split(','))

    def measure_voltage(self, channels=None) -> List[float]:
        """Measure one or more channels' actual output voltage.

        Returns
        -------
        list
            list of float values representing output voltages (in volts)
        """
        return floats(self._parent.query('MEAS%d:VOLT? (@%s)' %
                                         (self.number, self._channel_str_list(channels))).split(','))

    def measure_current(self, channels=None) -> List[float]:
        """Measure one or more channels' actual output current.

        Returns
        -------
        list
            list of float values representing output currents (in amps)
        """
        return floats(self._parent.query('MEAS%d:CURR? (@%s)' %
                                         (self.number, self._channel_str_list(channels))).split(','))

    def is_ready(self, channel):
        """Check if output channel voltage is ready (settled) or not."""

        self._parent.read_questionable_regs()

        if channel not in self.channels:
            return None
        else:
            return self.ready[channel - 1]

    def _set_ready(self, channel, ready):
        if channel in self.channels:
            self.ready[channel - 1] = ready

    def get_serial(self) -> str:
        return self._parent.query('CAL%d:SERIAL?' % self.number).strip('"')

    def set_calibration_state(self, channel, state):
        if channel in self.channels:
            self._parent.write('CAL%d:STATE (@%d),%s' % (self.number, channel, bool_to_str(state)))
        else:
            raise WrongChannel(self, channel)

    def get_calibration_state(self, channel):
        if channel in self.channels:
            return str_to_bool( self._parent.query('CAL%d:STATE? (@%d)' % (self.number, channel)) )
        else:
            raise WrongChannel(self, channel)

    def set_calibration_remark(self, remark):
        self._parent.write('CAL%d:REM %s' % (self.number, remark))

    def get_calibration_remark(self):
        return self._parent.query('CAL%d:REM?' % self.number).strip('"')

    def set_calibration_serial(self, serial):
        self._parent.write('CAL%d:SER %s' % (self.number, serial))

    def get_calibration_serial(self):
        return self._parent.query('CAL%d:SER?' % self.number).strip('"')

    def set_calibration_temperature(self, temperature):
        self._parent.write('CAL%d:TEMP %f' % (self.number, temperature))

    def get_calibration_temperature(self):
        return float(self._parent.query('CAL%d:TEMP?' % self.number))

    def update_calibration_time_and_temperature(self):
        self._parent.write('CAL%d:UPD' % self.number)

    def get_calibration_datetime(self):
        return datetime.fromisoformat(self._parent.query('CAL%d:DATE?' % self.number).strip('"'))

    def set_calibration_datetime(self, datetime_object : datetime):
        self._parent.write('CAL%d:DATE "%s"' % (self.number, datetime_object.strftime('%Y-%m-%d %H:%M:%S')))


    def set_calibration_output_range(self, channel, low, high):
        """Set output hardware limits."""
        if channel in self.channels:
            self._parent.write('CAL%d:OUTP:RANGE (@%d),%f,%f' % (self.number, channel, low, high))
        else:
            raise WrongChannel(self, channel)

