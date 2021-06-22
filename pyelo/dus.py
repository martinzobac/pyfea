import pyelo


class Dus(pyelo.Instrument):

    def __init__(self, parent: pyelo.Elo, number, name):
        super(Dus, self).__init__(parent, number, name)
        self.channels = (1, 2)
        self.ready = [True, True]
