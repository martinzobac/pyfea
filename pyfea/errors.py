class Error(Exception):
    pass


class WrongId(Error):
    def __init__(self, elo):
        super(WrongId, self).__init__(
            "Incorrect ID of %s: %s,%s" % (elo.visa_name, elo.vendor, elo.unit_name)
        )


class WrongInstrument(Error):
    def __init__(self, instrument):
        super(WrongInstrument, self).__init__(
            "Incorrect instrument %d" % instrument
        )


class ExpectedBooleanValue(Error):
    def __init__(self, value):
        super(ExpectedBooleanValue, self).__init__(
            "Expected boolean value, %s received instead " % value
        )


class FeaError(Error):
    def __init__(self, error_code, error_text):
        super( FeaError, self).__init__(
            "FEA error: %d, '%s'" % (error_code, error_text)
        )
        self.error_code = error_code
        self.error_text = error_text

class VISAError(Error):
    pass
