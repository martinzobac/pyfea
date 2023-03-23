import pyfea


class Eps(pyfea.Instrument):

    def __init__(self, parent: pyfea.Fea, number, name):
        super(Eps, self).__init__(parent, number, name)
        self.type = "EPS"
        self.ready = True
        self.max_voltage = 5000
        self.min_voltage = 0
        self.voltages = [0]

    def set_range(self, range, range2=None):
        if not range2:
            if range > 0:
                range = -range
            range2 = -range

        self._parent.write('OUTP%d:RANG %f' % (self.number, range) +
                           ', %f' % range2 if range2 else '')


