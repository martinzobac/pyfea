import pyelo


class Qbs(pyelo.Instrument):

    def __init__(self, parent: pyelo.Elo, number, name):
        super(Qbs, self).__init__(parent, number, name)
        self.type = "QBS"
        self.channels = (1, 2, 3, 4)
        self.ready = [True, True, True, True]
        self.max_voltage = 800
        self.min_voltage = -800
        self.voltages = [0, 0, 0, 0]

    def set_range(self, channels, range, range2=None):
        channels = self._channel_list(channels)
        if not range2:
            if range > 0:
                range = -range
            range2 = -range

        self._parent.write('OUTP%d:RANG (@%s),%f' % (self.number, self._channel_str_list(channels), range) +
                           ', %f' % range2 if range2 else '')


