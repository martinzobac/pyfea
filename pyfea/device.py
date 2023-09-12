"""Main FEA class

This file is part of PyFEA.

"""

import pyvisa
import pyfea
from pyfea.errors import *
from pyfea.constants import *
from pyvisa import constants
import ctypes
import threading
from typing import (Tuple, List)
from datetime import datetime

def bool_to_str(bool_value):
    if bool_value:
        return "1"
    else:
        return "0"

def str_to_bool(string):
    if (string=='0') | (string=='OFF'):
        return False
    elif (string=='1') | (string=='ON'):
        return True
    else:
        raise ExpectedBooleanValue(string)



def event_handler(resource, event, user_handle):
    """System Request callback function"""
    device = ctypes.cast(user_handle.value, ctypes.py_object).value
    # print('System request on %s' % device.visaName)
    device._event_callback()


class Fea:
    """Main FEA class"""

    def __init__(self, visa_name=None):
        """Object constructor"""

        self._semaphore = threading.BoundedSemaphore(value=1)
        self.stb = 0
        self.esr = 0
        self.error = False
        self.visa_name = None
        self._visa = None
        self.vendor = ""
        self.unit_name = ""
        self.serial = ""
        self.fw_version = ""
        self.instrument_nums = []
        self.instrument_names = []
        self._instruments = []
        self.instrument_selected = None
        self._handler = None
        self._wrapped_handler = None
        self._opened = False

        self.aps = None
        self.esp = None
        self.sps = None

        if visa_name:
            self.open(visa_name)

    def __delete__(self):
        self.close()

    from pyfea.instrument import Instrument

    @property
    def instruments(self) -> List[Instrument]:
        return self._instruments

    def open(self, visa_name):
        if self.is_opened():
            return

        self.visa_name = visa_name

        try:
            pm = pyvisa.ResourceManager()
            self._visa = pm.open_resource(visa_name)
            self._visa.read_termination = '\n'
            self._visa.write_termination = '\n'
            self._visa.timeout = 10000
            self._visa.query_delay = 0.0
            self._visa.clear()
        except pyvisa.errors.VisaIOError:
            raise pyfea.errors.VISAError

        self.init()

        idn = self.query('*IDN?').split(',')
        self.vendor = idn[0]
        self.unit_name = idn[1]
        self.serial = idn[2]
        self.fw_version = idn[3]

        if self.unit_name != FEA_NAME:
            raise WrongId(self)

        self.instrument_nums, self.instrument_names = self.read_instrument_list()
        self._instruments = []
        for name, num in zip(self.instrument_names, self.instrument_nums):

            new_object = None
            if name.startswith('EPS'):
                self.eps = pyfea.Eps(self, num, name)
                new_object = self.eps
            elif name.startswith('SPS'):
                self.sps = pyfea.Sps(self, num, name)
                new_object = self.sps
            elif name.startswith('APS'):
                self.aps = pyfea.Aps(self, num, name)
                new_object = self.aps
            elif name.startswith('AMP'):
                self.amm = pyfea.Amm(self, num, name)
                new_object = self.amm
            else:
                raise pyfea.errors.WrongInstrument( num )

            if new_object:
                self._instruments.append(new_object)

        self.instrument_selected = None
        self._wrapped_handler = self._visa.wrap_handler(event_handler)
        self._handler = self._visa.install_handler(constants.EventType.service_request, self._wrapped_handler, id(self))
        self._visa.enable_event(constants.EventType.service_request, constants.EventMechanism.handler, None)
        self._opened = True

    def close(self):
        if self.is_opened():
            self._visa.disable_event(constants.EventType.service_request, constants.EventMechanism.handler)
            self._visa.uninstall_handler(constants.EventType.service_request, self._wrapped_handler, self._handler)
            self._visa.close()
            self.stb = 0
            self.esr = 0
            self.error = False
            self.visa_name = None
            self._visa = None
            self.vendor = ""
            self.unit_name = ""
            self.serial = ""
            self.fw_version = ""
            self.instrument_nums = None
            self.instrument_names = None
            self._instruments = None
            self.instrument_selected = None
            self._handler = None
            self._opened = False

    def is_opened(self):
        return self._opened

    def _lock(self):
        """Acquire lock for the resource"""
        self._semaphore.acquire()



    def _unlock(self):
        """Release lock for the resource"""
        self._semaphore.release()

    def write(self, command, check_errors=True, lock=True):
        """Send command string to the ELO device.

        Parameters
        ----------
        command : str
            SCPI command string to be sent to the ELO
        check_errors : bool
            When True the STB register error flag will be tested and in case the flag is true the error
            is popped from the queue.
        lock : bool
            When True the resource lock is acquired before accessing the interface.
        """
        if lock:
            self._lock()
        try:
            self._visa.write(command)
        except pyvisa.errors.VisaIOError:
            raise VISAError
        finally:
            if lock:
                self._unlock()

        if check_errors:
            self._check_for_error()

    def query(self, query, check_errors=True, lock=True, time_out=None) -> str:
        """Send query string to the ELO device and retrieve a response.

        Parameters
        ----------
        query : str
            SCPI command string to be sent to the ELO
        check_errors : bool
            When True the STB register error flag will be tested and in case the flag is true the error
            is popped from the queue.
        lock : bool
            When True the resource lock is acquired before accessing the interface.
        time_out : int
            Maximal time to wait for response (in milliseconds). (not implemented yet)

        Returns
        -------
        str
            Response string received from the remote device.
        """
        if lock:
            self._lock()
        try:
            response = self._visa.query(query)
        except pyvisa.errors.VisaIOError:
            raise VISAError
        finally:
            if lock:
                self._unlock()

        if check_errors:
            self._check_for_error()

        return response

    def get_stb(self) -> int:
        """Read device's Status Byte register.

        Returns
        -------
        int
            Status Byte.
        """
        self.stb = self._visa.read_stb()
        return self.stb

    def init(self):
        """Restart ELO and configure event registers."""
        self._visa.clear()
        self._visa.write('*CLS;')
        #self._visa.write('*SRE %d' % (pyelo.constants.STB_ERR + pyelo.constants.STB_QES))  # enable ERR and QES
        self._visa.write('*ESE %d' % ESR_OPC)  # enable OPC

    def get_esr(self):
        self.esr = int(self.query('*ESR?'))
        return self.esr

    def read_instrument_list(self) -> Tuple[List[int], List[str]]:
        """Read list of installed ELO's instruments (modules).

        Returns
        -------

        List[int]
            List of SCPI logical numbers of installed modules.
        List[str]
            List of SCPI logical names of installed modules.
        """
        catalog = self.query('INST:CAT:FULL?').split(',')
        names = []
        nums = []
        for name, num in zip(catalog[::2], catalog[1::2]):
            names.append(name.strip('"'))
            nums.append(int(num))
        return nums, names

    def wait_for_operation_complete(self, timeout=15000):
        """Wait for finishing of previous (pending) operations ."""
        self.query('*OPC?', time_out=timeout)

    def select_instrument(self, inst_num: int):
        """Select one of virtual instruments.

        Parameters
        ----------
        inst_num
            logical SCPI number
        """
        if inst_num not in self.instrument_nums:
            raise WrongInstrument(inst_num)
        if self.instrument_selected != inst_num:
            self.write('INST:NSEL %d' % inst_num)
            self.instrument_selected = inst_num

    def read_error(self) -> Tuple[int, str]:
        """Retrieve one error from the error queue.

        Returns
        -------
        int
            Error code
        str
            Error description
        """
        try:
            error = self._visa.query('SYST:ERROR?').split(',')
        except pyvisa.errors.VisaIOError:
            return None

        error_code = int(error[0])
        error_text = error[1][1:-1]

        self._event_callback()

        return error_code, error_text

    def _check_for_error(self):
        """Read STB register and if any error in the queue read it and raise exception."""
        if self.get_stb() & 4:
            error_code, error_text = self.read_error()
            raise FeaError(error_code, error_text)


    def get_instrument_by_number(self, number: int) -> Instrument:
        """Get virtual instrument object according to SCPI logical number.

        Parameters
        ----------
        number
            SCPI logical number

        Returns
        -------
        pyelo.Instrument
            Instrument object or None if instrument not found
        """
        for inst in self._instruments:
            if inst.number == number:
                return inst

        return None

    def read_questionable_regs(self):
        """Read questionable register tree and set appropriate flags in instruments' objects."""
        self._lock()
        try:
            event = int(self.query('STAT:QUES?', False, lock=False))
            if event & pyfea.constants.QUEST_INST_SUM:
                inst_event = int(self.query('STAT:QUES:INST?', False, lock=False))
                for inst in self._instruments:
                    if inst_event & (1 << inst.number):
                        isum_event = int(self.query('STAT:QUES:INST%d:ISUM?' % inst.number, False, lock=False))
                        for channel in inst.channels:
                            if isum_event & (1 << channel):
                                channel_event = int(self.query('STAT:QUES:INST%d:ISUM? (@%d)' %
                                                               (inst.number, channel), False, lock=False))
                                channel_cond = int(self.query('STAT:QUES:INST%d:ISUM:COND? (@%d)' %
                                                              (inst.number, channel), False, lock=False))

                                if channel_event & pyfea.constants.QUEST_VOLTAGE:
                                    inst._set_ready(channel, not channel_cond & pyfea.constants.QUEST_VOLTAGE)
                                    # print('Inst. %s/channel %d is %sready' %
                                    #      (inst.name, channel, 'NOT ' if not inst.is_ready(channel) else ''))
        finally:
            self._unlock()

    def _event_callback(self):
        stb = self.get_stb()
        # print('STB: %02x' % stb)

        if stb & pyfea.constants.STB_QES:
            self.read_questionable_regs()

        if stb & pyfea.constants.STB_ERR:
            self.error = True
        else:
            self.error = False

    def is_operation_completed(self) -> bool:
        fea.write('*OPC')
        if self.get_stb() & pyfea.constants.STB_ESR:
            return self.get_esr() & pyfea.constants.ESR_OPC != 0
        else:
            return False

    def turn_on(self, instruments=None, wait=True, delay=0):
        if not instruments:
            instruments = self._instruments
        for instrument in instruments:
            instrument.turn_on(wait)
            if not wait:
                sleep(delay)

    def turn_off(self, instruments=None, wait=True):
        if not instruments:
            instruments = self._instruments
        for instrument in instruments:
            instrument.turn_off(wait)

    def set_calibration_mode(self, mode, password=None):
        if mode:
            self.write('CAL:MODE ON,"%s"' % password)
        else:
            self.write('CAL:MODE OFF')

    def get_calibration_mode(self):
        return int(self.query('CAL:MODE?')) != 0

    def set_calibration_password(self, old_password, new_password):
        self.write('CAL:PASS:NEW "%s","%s"' % (old_password, new_password))

    def get_serial(self) -> str:
        return self.query('CAL:SERIAL?').strip('"')

    def set_calibration_state(self, state):
        self.write('CAL:STATE %s' % (bool_to_str(state)))

    def get_calibration_state(self):
        return str_to_bool(self.query('CAL:STATE?'))

    def set_calibration_remark(self, remark):
        self.write('CAL:REM "%s"' % remark)

    def get_calibration_remark(self):
        return self.query('CAL:REM?').strip('"')

    def set_calibration_serial(self, serial):
        self.write('CAL:SER %s' % serial)

    def get_calibration_serial(self):
        return self.query('CAL:SER?' % self.number).strip('"')

    def set_calibration_temperature(self, temperature):
        self.write('CAL:TEMP %f' % temperature)

    def get_calibration_temperature(self):
        return float(self.query('CAL:TEMP?'))

    def update_calibration_time_and_temperature(self):
        self.write('CAL:UPD' )

    def get_calibration_datetime(self):
        return datetime.fromisoformat(self.query('CAL:DATE?' ).strip('"'))

    def set_calibration_datetime(self, datetime_object : datetime):
        self.write('CAL:DATE "%s"' % (datetime_object.strftime('%Y-%m-%d %H:%M:%S')))

    def save_calibration(self):
        self.write('CAL:SAVE')

    def load_calibration(self):
        self.write('CAL:LOAD')


if __name__ == '__main__':
    fea = Fea('GPIB::22::INSTR')
    fea.init()

    print('Vendor: %s' % fea.vendor)
    print('Unit: %s' % fea.unit_name)
    print('Serial: %s' % fea.serial)
    print('Fw version: %s' % fea.fw_version)
    print('Instruments: %s' % ', '.join(fea.instrument_names))

    instruments = fea._instruments

    from time import sleep

    print('Starting EPS')
    fea.eps.set_voltage(2000)
    fea.eps.turn_on(False)
    sleep(0.1)

    print('Waiting for OPC')
    fea.wait_for_operation_complete()

    done = False
    timer = 10
    while not done:
        for instrument in instruments:
            voltage = instrument.measure_voltage()
            print('%s voltage: %.2f V' % (instrument.name, voltage))
            # currents = instrument.measure_current(instrument.channels)
            # print('%s currents: %s' % (instrument.name, ', '.join(['%.2f uA' % (val * 1e6) for val in currents])))
        sleep(0.5)
        ready = fea.is_operation_completed()
        if ready:
            if timer > 0:
                timer -= 1
            else:
                done = True

        # input('Press ENTER to continue')

    for instrument in instruments:
        instrument.turn_off()
