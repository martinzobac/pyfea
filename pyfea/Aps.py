import pyfea


class Aps(pyfea.Supply):

    def __init__(self, parent: pyfea.Fea, number, name):
        super().__init__(parent, number, name)
        self.type = "APS"
        self.ready = True
        self.max_voltage = 10000
        self.min_voltage = 0
        self.max_norm_prog = 0.8        # maximal normalized voltage program value

