import pyelo


class Qbs(pyelo.Instrument):

    def __init__(self, parent: pyelo.Elo, number, name):
        super(Qbs, self).__init__(parent, number, name)
        self.channels = (1, 2, 3, 4)
        self.ready = [True, True, True, True]

