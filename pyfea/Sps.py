import pyfea


class Sps(pyfea.Instrument):

    def __init__(self, parent: pyfea.Fea, number, name):
        super(Sps, self).__init__(parent, number, name)
        self.type = "SPS"
        self.ready = True
        self.max_voltage = 0
        self.min_voltage = 1500
        self.voltages = [0]

