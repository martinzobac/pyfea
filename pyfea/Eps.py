import pyfea


class Eps(pyfea.Supply):

    def __init__(self, parent: pyfea.Fea, number, name):
        super().__init__(parent, number, name)
        self.type = "EPS"
        self.ready = True
        self.max_voltage = 5000
        self.min_voltage = 0
        self.max_norm_prog = 0.9        # maximal normalized voltage program value

