import pyvisa
import pyelo
from pyelo.errors import *
from pyvisa import constants
import ctypes
import threading


def event_handler(resource, event, user_handle):
    device = ctypes.cast(user_handle.value, ctypes.py_object).value
    print('System request on %s' % device.visaName)
    device._event_callback()


class Elo:
    def __init__(self, visa_name):
        self.visaName = visa_name

        self._semaphore = threading.BoundedSemaphore(value=1)

        pm = pyvisa.ResourceManager()

        self._visa = pm.open_resource(visa_name)
        self._visa.read_termination = '\n'
        self._visa.write_termination = '\n'
        self._visa.timeout = 10000
        self._visa.query_delay = 0.00
        self._visa.clear()
        self.stb = 0

        self.reset()
        idn = self.query('*IDN?').split(',')
        self.vendor = idn[0]
        self.unit_name = idn[1]
        self.serial = idn[2]
        self.fw_version = idn[3]

        if self.vendor != pyelo.constants.ELO_VENDOR or idn[1] != pyelo.constants.ELO_NAME:
            raise WrongId(self)

        self.instrument_nums, self.instrument_names = self.read_instrument_list()
        self.instruments = []
        for name, num in zip(self.instrument_names, self.instrument_nums):
            new_object = None
            if name.startswith('QBS'):
                new_object = pyelo.Qbs(self, num, name)
            elif name.startswith('DUS'):
                new_object = pyelo.Dus(self, num, name)
            self.instruments.append(new_object)

        self.instrument_selected = None
        self._handler = self._visa.install_handler(constants.EventType.service_request,
                                                   self._visa.wrap_handler(event_handler),
                                                   id(self))
        self._visa.enable_event(constants.EventType.service_request, constants.EventMechanism.handler, None)

    def __delete__(self):
        self._visa.disable_event(constants.EventType.service_request, constants.EventMechanism.handler)
        self._visa.uninstall_handler(constants.EventType.service_request, self._visa.wrap_handler(event_handler),
                                     self._handler)
        self._visa.close()

    def _lock(self):
        self._semaphore.acquire()

    def _unlock(self):
        self._semaphore.release()

    def write(self, command, check_errors=True, lock=True):
        if lock: self._lock()
        try:
            self._visa.write(command)
        finally:
            if lock: self._unlock()

        if check_errors:
            self._check_for_error()

    def query(self, query, check_errors=True, lock=True):
        if lock: self._lock()
        try:
            response = self._visa.query(query)
        finally:
            if lock: self._unlock()

        if check_errors:
            self._check_for_error()

        return response

    def _read_stb(self):
        self.stb = self._visa.read_stb()
        return self.stb

    def reset(self):
        self._visa.clear()
        self._visa.write('*RST;*CLS;')
        self._visa.write('*SRE 12')  # enable ERR and QES

    def read_instrument_list(self):
        catalog = self.query('INST:CAT:FULL?').split(',')
        names = []
        nums = []
        for name, num in zip(catalog[::2], catalog[1::2]):
            names.append(name.strip('"'))
            nums.append(int(num))
        return nums, names

    def wait_for_operation_complete(self):
        self.query('*OPC?')

    def select_instrument(self, inst_num: int):
        if inst_num not in self.instrument_nums:
            raise WrongInstrument(inst_num)
        if self.instrument_selected != inst_num:
            self.write('INST:NSEL %d' % inst_num)
            self.instrument_selected = inst_num

    def _read_error(self):
        try:
            error = self._visa.query('SYST:ERROR?').split(',')
        except pyvisa.errors.VisaIOError:
            return None

        error_code = int(error[0])
        error_text = error[1][1:-1]

        return error_code, error_text

    def _check_for_error(self):
        if self._read_stb() & 4:
            error_code, error_text = self._read_error()
            raise EloError(error_code, error_text)

    def get_instrument_by_number(self, number: int):
        for inst in self.instruments:
            if inst.number == number:
                return inst

        return None

    def _read_questionable_regs(self):
        self._lock()
        try:
            event = int(self.query('STAT:QUES?', False, lock=False))
            if event & pyelo.constants.QUEST_INST_SUM:
                inst_event = int(self.query('STAT:QUES:INST?', False, lock=False))
                for inst in self.instruments:
                    if inst_event & (1 << inst.number):
                        isum_event = int(self.query('STAT:QUES:INST%d:ISUM?' % inst.number, False, lock=False))
                        for channel in inst.channels:
                            if isum_event & (1 << channel):
                                channel_event = int(self.query('STAT:QUES:INST%d:ISUM? (@%d)' %
                                                                     (inst.number, channel), False, lock=False))
                                channel_cond = int(self.query('STAT:QUES:INST%d:ISUM:COND? (@%d)' %
                                                                    (inst.number, channel), False, lock=False))

                                if channel_event & pyelo.constants.QUEST_VOLTAGE:
                                    inst.set_ready(channel, not channel_cond & pyelo.constants.QUEST_VOLTAGE)
                                    print('Inst. %s/channel %d is %sready' %
                                          (inst.name, channel, 'NOT ' if not inst.is_ready(channel) else ''))
        finally:
            self._unlock()

    def _event_callback(self):
        stb = self._read_stb()
        print('STB: %02x' % stb)
        while stb & pyelo.constants.STB_ERR:
            error_code, error_text = self.__read_error()
            raise EloError(error_code, error_text)
            stb = self._read_stb()

        if stb & pyelo.constants.STB_QES:
            self._read_questionable_regs()

        self._check_for_error()


if __name__ == '__main__':
    elo = Elo('GPIB::22::INSTR')
    elo.reset()

    print('Vendor: %s' % elo.vendor)
    print('Unit: %s' % elo.unit_name)
    print('Serial: %s' % elo.serial)
    print('Fw version: %s' % elo.fw_version)
    print('Instruments: %s' % elo.instrument_names)

    from time import sleep

    for instrument in elo.instruments:
        instrument.turn_on(False)
        sleep(0.1)

    elo.wait_for_operation_complete()

    for instrument in elo.instruments:
        instrument.turn_on_channels(instrument.channels)
        instrument.set_voltage(instrument.channels, 500 if isinstance(instrument, pyelo.Qbs) else -2000)

    elo.wait_for_operation_complete()

    sleep(2)

    for instrument in elo.instruments:
        voltages = instrument.measure_voltage(instrument.channels)
        print('%s voltages: %s' % (instrument.name, ', '.join(['%.2f V' % val for val in voltages])))
        currents = instrument.measure_current(instrument.channels)
        print('%s currents: %s' % (instrument.name, ', '.join(['%.2f uA' % (val*1e6) for val in currents])))

    # input('Press ENTER to continue')

    for instrument in elo.instruments:
        instrument.turn_off()
