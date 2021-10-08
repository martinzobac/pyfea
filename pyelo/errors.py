class Error(Exception):
    pass


class WrongId(Error):
    def __init__(self, elo):
        super(WrongId, self).__init__(
            "Incorrect ID of %s: %s,%s" % (elo.visaName, elo.vendor,elo.unit_name)
        )


class WrongInstrument(Error):
    def __init__(self, instrument):
        super(WrongId, self).__init__(
            "Incorrect instrument %d" % instrument
        )


class WrongChannel(Error):
    def __init__(self, instrument, channel):
        super(WrongChannel, self).__init__(
            "Incorrect channel %d " % channel
        )

class ExpectedBooleanValue(Error):
    def __init__(self, value):
        super(ExpectedBooleanValue, self).__init__(
            "Expected boolean value, %s received instead " % value
        )


class EloError(Error):
    def __init__(self, error_code, error_text):
        super( EloError, self).__init__(
            "ELO error: %d, '%s'" % (error_code, error_text)
        )
        self.error_code = error_code
        self.error_text = error_text

class VISAError(Error):
    pass
