from pyfea import Fea
import random
from time import sleep

if __name__ == '__main__':

    fea = Fea('GPIB::22::INSTR')
    fea.init()

    print('Vendor: %s' % fea.vendor)
    print('Unit: %s' % fea.unit_name)
    print('Serial: %s' % fea.serial)
    print('Fw version: %s' % fea.fw_version)
    print('Instruments: %s' % ', '.join(fea.instrument_names))

    print('Autozeroing...')
    fea.amm.auto_zero(True)
    fea.wait_for_operation_complete()
    print('Done.')
    fea.amm.zero_check(False)

    fea.aps.set_rise_rate(1000)
    fea.aps.set_fall_rate(1000)
    fea.eps.set_rise_rate(500)
    fea.eps.set_fall_rate(500)
    fea.sps.set_rise_rate(150)
    fea.sps.set_fall_rate(150)
    fea.aps.turn_on()

    try:
        while True:

            voltage1 = random.random()*10000
            voltage2 = random.random()*5000
            voltage3 = random.random()*1500
            print( "Voltages: %f V" % voltage1 )
            fea.aps.set_voltage( voltage1 )
            fea.eps.set_voltage( voltage2 )
            fea.sps.set_voltage( voltage3 )
            fea.wait_for_operation_complete()
            sleep(1)

    except KeyboardInterrupt:
        pass