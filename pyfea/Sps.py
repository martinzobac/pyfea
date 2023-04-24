import pyfea


class Sps(pyfea.Supply):

    def __init__(self, parent: pyfea.Fea, number, name):
        super().__init__(parent, number, name)
        self.type = "SPS"
        self.ready = True
        self.max_voltage = 0
        self.min_voltage = 1500
        self.max_norm_prog = 0.6        # maximal normalized voltage program value

