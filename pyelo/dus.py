import pyelo


class Dus(pyelo.Instrument):

    def __init__(self, parent: pyelo.Elo, number, name):
        super(Dus, self).__init__(parent, number, name)
        self.type = "DUS"
        self.channels = (1, 2)
        self.ready = [True, True]
        self.max_voltage = 0
        self.min_voltage = -5000
        self.voltages = [0, 0]

