import pyelo
from pyelo.errors import *


def floats(string_list):
    return [float(value) for value in string_list]


class Instrument:
    def __init__(self, parent: pyelo.Elo, number, name):
        self._parent = parent
        self.number = number
        self.name = name
        self.channels = ()
        self.ready = []

    def turn_on(self, wait=True):
        self._parent.write('INST%d:STAT ON' % self.number)
        if wait:
            self._parent.wait_for_operation_complete()

    def turn_off(self, wait=True):
        self._parent.write('INST%d:STAT OFF' % self.number)
        if wait:
            self._parent.wait_for_operation_complete()

    def _channel_list(self, channels):
        string = ''
        for channel in channels:
            if channel not in self.channels:
                raise WrongChannel(self, channel)
            else:
                if string != '': string += ','
                string += str(channel)
        return string

    def turn_on_channels(self, channels):
        self._parent.write('OUTP%d:STAT (@%s),ON' % (self.number, self._channel_list(channels)))

    def turn_off_channels(self, channels):
        self._parent.write('OUTP%d:STAT (@%s),OFF' % (self.number, self._channel_list(channels)))

    def set_voltage(self, channels: int, voltage: float):
        self._parent.write('SOUR%d:VOLT (@%s),%fV' % (self.number, self._channel_list(channels), voltage))

    def measure_voltage(self, channels):
        return floats(self._parent.query('MEAS%d:VOLT? (@%s)' %
                                                  (self.number, self._channel_list(channels))).split(','))

    def measure_current(self, channels):
        return floats(self._parent.query('MEAS%d:CURR? (@%s)' %
                                                  (self.number, self._channel_list(channels))).split(','))

    def is_ready(self, channel):
        if channel not in self.channels:
            return None
        else:
            return self.ready[channel-1]

    def set_ready(self, channel, ready):
        if channel in self.channels:
            self.ready[channel-1] = ready
