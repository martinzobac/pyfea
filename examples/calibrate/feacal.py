from matplotlib import pyplot as plt
import numpy as np
from pyfea import Fea
import pyvisa
from time import sleep

global fea, voltage_meter, current_meter

voltage_probe_div_ratio = 1000

def mean(values):
    return np.array(values).mean()

def open_devices():
    global fea, voltage_meter, current_meter

    fea = Fea('GPIB::22::INSTR')
    fea.init()

    print('Vendor: %s' % fea.vendor)
    print('Unit: %s' % fea.unit_name)
    print('Serial: %s' % fea.serial)
    print('Fw version: %s' % fea.fw_version)
    print('Instruments: %s' % ', '.join(fea.instrument_names))

    pm = pyvisa.ResourceManager()
    voltage_meter = pm.open_resource('34470A')
    voltage_meter.write('*RST')
    voltage_meter.write('*CLS')
    voltage_meter.write('CONF:VOLT:DC 10V')
    voltage_meter.write('VOLT:NPLC 1')
    voltage_meter.write('VOLT:ZERO:AUTO ONCE')

    current_meter = pm.open_resource('34461B')
    current_meter.write('*RST')
    current_meter.write('*CLS')
    current_meter.write('CONF:CURR:DC 100uA')
    current_meter.write('CURR:NPLC 1')
    current_meter.write('CURR:ZERO:AUTO ONCE')


def qcom_calibration(xps, test_levels):
    global fea, voltage_meter, current_meter

    print('=== Measuring quiescent current of %s ===' % xps.name)

    print('Enabling calibration mode')
    fea.set_calibration_mode(True, '1234')

    print('Saving program calibration')
    program_cal_points = xps.get_program_calibration_points()

    print('Disabling program scaling')
    xps.set_program_calibration_points([(0, 0), (1, 1)])

    print('Turning on %s' % xps.name)
    xps.set_voltage(0)
    xps.turn_on(True)
    sleep(0.5)

    cal_quiescent_points = []
    xps.quiescent_compensation(False)

    voltage_adc_vec = []
    current_adc_vec = []

    print('Iterating program levels ')
    for level in test_levels:
        xps.set_voltage(level)
        sleep(2)
        voltage_adc_values = []
        current_adc_values = []
        for i in range(0, 10):
            voltage_adc_values.append(xps.measure_voltage_adc())
            current_adc_values.append(xps.measure_current_adc())
            print('.', end='')
            sleep(0.2)

        voltage_adc = mean(voltage_adc_values)
        current_adc = mean(current_adc_values)
        cal_quiescent_points.append((voltage_adc, current_adc))
        print('\rLevel %f, voltage ADC: %.3f, current ADC: %.3f' % (level, voltage_adc, current_adc))
        voltage_adc_vec.append(voltage_adc)
        current_adc_vec.append(current_adc)

    print('Turning supply off and waiting')
    xps.turn_off(True)
    xps.set_voltage(0)

    # Restore program cal points
    xps.set_program_calibration_points(program_cal_points)

    ax = plt.subplot(211)
    ax.cla()
    ax.plot(test_levels, np.array(voltage_adc_vec) * 100)
    plt.ylabel("Voltage (%)")
    ax.grid()
    ax = plt.subplot(212)
    ax.cla()
    ax.plot(test_levels, np.array(current_adc_vec) * 100)
    plt.ylabel("Current (%)")
    ax.grid()
    plt.show(block=True)

    store_qcom = input('Store QCOM data? y/n')
    if store_qcom and store_qcom.lower()[0] == 'y':
        # Set newly acquired quiescent current compensation points
        xps.set_quiscent_compensation_points(cal_quiescent_points)
        # Turn qcom on
        xps.quiescent_compensation(True)


def do_calibration(xps, test_levels):
    print('=== Measuring program and monitors of %s ===' % xps.name)

    print('Enabling calibration mode')
    fea.set_calibration_mode(True, '1234')

    print('Saving program calibration')
    program_cal_points = xps.get_program_calibration_points()

    print('Disabling program scaling')
    xps.set_program_calibration_points([(0, 0), (1, 1)])

    print('Turning on %s' % xps.name)
    xps.set_voltage(0)
    xps.turn_on(True)
    sleep(0.5)

    voltage_adc_vec = []
    current_adc_vec = []
    voltage_ext_vec = []
    current_ext_vec = []

    for level in test_levels:
        xps.set_voltage(level)
        sleep(2)

        voltage_ext_values = []
        current_ext_values = []
        voltage_adc_values = []
        current_adc_values = []

        print( 'Level %f ' % level, end='')
        for i in range(0, 10):
            voltage_adc_values.append(xps.measure_voltage_adc())
            current_adc_values.append(xps.measure_current_adc())
            voltage_ext_values.append(float(voltage_meter.query("READ?")) * voltage_probe_div_ratio)
            current_ext_values.append(float(current_meter.query("READ?")))
            print('.', end='')
            sleep(0.2)

        voltage_adc = mean(voltage_adc_values)
        current_adc = mean(current_adc_values)
        voltage_ext = mean(voltage_ext_values)
        current_ext = mean(current_ext_values)

        print('\rLevel %f, voltage ADC/EXT: %.3f/%.3f V, current ADC/EXT: %.3f/%.3f uA' %
              (level,
               voltage_adc, voltage_ext,
               current_adc, current_ext*1e6))

        voltage_adc_vec.append(voltage_adc)
        current_adc_vec.append(current_adc)
        voltage_ext_vec.append(voltage_ext)
        current_ext_vec.append(current_ext)

    print('Turning supply off and waiting')
    xps.turn_off(True)
    xps.set_voltage(0)

    # Restore program cal points
    xps.set_program_calibration_points(program_cal_points)

    plt.figure(1)
    ax = plt.subplot(221)
    ax.cla()
    ax.plot(test_levels, np.array(voltage_adc_vec) * 100)
    plt.ylabel("Voltage (%)")
    ax.grid()

    ax = plt.subplot(222)
    ax.cla()
    ax.plot(test_levels, voltage_ext_vec)
    plt.ylabel("Voltage (V)")
    ax.grid()

    ax = plt.subplot(223)
    ax.cla()
    ax.plot(test_levels, np.array(current_adc_vec) * 100)
    plt.ylabel("Current (%)")
    ax.grid()

    ax = plt.subplot(224)
    ax.cla()
    ax.plot(test_levels, np.array(current_ext_vec) * 1e6)
    plt.ylabel("Current (uA)")
    ax.grid()

    plt.show(block=True)

    store_cal = input('Set calibration data?')
    if store_cal and store_cal.lower()[0] == 'y':
        print( 'Set newly acquired cal. data' )
        xps.set_program_calibration_points(list(zip(abs(np.array(voltage_ext_vec)), test_levels)))
        xps.set_vmonit_calibration_points(list(zip(voltage_adc_vec, voltage_ext_vec)))
        xps.set_imonit_calibration_points(list(zip(current_adc_vec, current_ext_vec)))


if __name__ == '__main__':

    open_devices()

    # xps = fea.eps
    # test_levels = np.linspace(0, 0.9, 5)

    xps = fea.sps
    test_levels = np.linspace(0, 0.6, 5)

    print('Turning supply off and waiting')
    xps.turn_off(True)
    xps.set_voltage(0)
    sleep(3)

    do_qcom = input('Disconnect output load and enter "y" to do quiescent compensation:')
    if do_qcom and do_qcom.lower()[0] == 'y':
        qcom_calibration(xps, test_levels)

    do_cal = input('Connect output load and enter "y" to do program and monitors calibration:')
    if do_cal and do_cal.lower()[0] == 'y':
        do_calibration(xps, test_levels)

    save_cal = input('Save calibration? ')
    if save_cal and save_cal.lower()[0] == 'y':
        fea.save_calibration()

