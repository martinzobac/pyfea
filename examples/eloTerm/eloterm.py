from blessed import Terminal
from pyelo import Elo
import pyelo.errors
from editor import editor
from time import perf_counter
import signal

global error_display_time
error_display_time = None


def show_error(term, error_code= None, error_text=''):
    global error_display_time

    print(term.move_yx(term.height-3, 0) +
          term.center('' if not error_code else term.red('Error %d: "%s"' % (error_code, error_text))))
    if error_code:
        error_display_time = perf_counter()


def show_instrument_name(inst, selected, channel=None):
    return (term.blue if not inst.state else term.green) + \
          (term.underline if selected else '') + \
          inst.name + term.normal


def change_instrument_state(inst, channel=None):
    if inst.get_state():
        inst.turn_off(wait=False)
    else:
        inst.turn_on(wait=False)


def show_instrument_serial(inst, selected, channel=None):
    return 'S/N: ' + inst.serial


def show_instrument_temperature(inst, selected, channel=None):
    return '%.2f °C' % inst.temperature


def show_instrument_range_low(inst, selected, channel=None):
    return (term.underline if selected else '') + \
          '%.1f V' % inst.range[0] + term.normal


def show_instrument_range_high(inst, selected, channel=None):
    return (term.underline if selected else '') + \
          '%.1f V' % inst.range[1] + term.normal


def change_instrument_range_low(inst, channel=None):
    try:
        new_value = float(editor(term, 10, ''))   # str(inst.range[0])))
        inst.set_range(inst.channels, new_value, inst.range[1])
    except ValueError:
        pass


def change_instrument_range_high(inst, channel=None):
    try:
        new_value = float(editor(term, 10, ''))    # str(inst.range[1])))
        inst.set_range(inst.channels, inst.range[0], new_value)
    except ValueError:
        pass


def show_channel_state(inst, selected, channel=None):
    if not inst.channels_state[channel-1]:
        color = term.blue
    elif inst.is_ready(channel):
        color = term.green
    else:
        color = term.blink_red

    return (color + \
           (term.underline if selected else '') + \
           ' Channel %d' % channel + \
           term.normal )


def change_channel_state(inst, channel=None):
    if inst.get_channels_state((channel,))[0]:
        inst.turn_off_channels((channel,))
    else:
        inst.turn_on_channels((channel,))


def show_channel_setpoint(inst, selected, channel=None):
    return (term.underline if selected else '') + \
          '[%7.2f V]' % inst.get_voltage(channel)[0] + \
          term.normal


def change_channel_setpoint(inst, channel=None):
    try:
        new_value = float(editor(term, 10, ''))  # str(inst.get_voltage(channel)[0])))
        inst.set_voltage(channel, new_value)
    except ValueError:
        pass


def show_channel_voltage(inst, selected, channel=None):
    return '%7.2f V' % inst.measured_voltages[channel-1] + term.normal


def show_channel_current(inst, selected, channel=None):
    return '%7.2f µA' % (inst.measured_currents[channel-1]*1e6) + term.normal


lines = []


def setup_screen():
    global lines

    print(term.home + term.clear, end='')

    columns3 = range(0, term.width, int(term.width / 3))
    n = len(elo._instruments)
    for index, inst in enumerate(elo._instruments, 0):
        inst.column = index
        inst.col_pos = int(round((index / n * term.width)))
        inst.col_width = int(round(((index+1) / n * term.width))) - inst.col_pos
        inst.max_row = len(inst.channels)*2+2

    lines = [
        {"y": 6, "on_show": show_instrument_name, "on_enter": change_instrument_state, "channel": None},
        {"y": 7, "on_show": show_instrument_serial, "on_enter": None, "channel": None},
        {"y": 8, "on_show": show_instrument_temperature, "on_enter": None, "channel": None},
        {"y": 9, "on_show": show_instrument_range_low, "on_enter": change_instrument_range_low, "channel": None},
        {"y":10, "on_show": show_instrument_range_high, "on_enter": change_instrument_range_high, "channel": None},
    ]
    for ch in (1, 2, 3, 4):
        lines += [
            {"y": 7+ch*4+0, "on_show": show_channel_state, "on_enter": change_channel_state, "channel": ch},
            {"y": 8+ch*4, "on_show": show_channel_setpoint, "on_enter": change_channel_setpoint, "channel": ch},
            {"y": 9+ch*4, "on_show": show_channel_voltage, "on_enter": None, "channel": ch},
            {"y": 10+ch*4, "on_show": show_channel_current, "on_enter": None, "channel": ch},
        ]

    print(term.home + term.clear, end='')
    print(term.move_y(1) + term.center('ELO-NCK control utility', fillchar='='), end='')
    print(term.move_yx(3, columns3[0]) + term.black_on_darkgreen(' Vendor: ') + ' ' + elo.vendor, end='')
    print(term.move_yx(3, columns3[1]) + term.black_on_darkgreen(' Unit: ') + ' ' + elo.unit_name, end='')
    print(term.move_yx(3, columns3[2]) + term.black_on_darkgreen(' VISA name: ') + ' ' + visa_name, end='')
    print(term.move_yx(4, columns3[1]) + term.black_on_darkgreen(' Serial: ') + ' ' + elo.serial, end='')
    print(term.move_yx(4, columns3[2]) + term.black_on_darkgreen(' Fw version: ') + ' ' + elo.fw_version, end='')

    print(term.move_yx(term.height-2, 0) +
          term.center('press Q/q to exit, A/a to turn on/off all', term.width), end='')


def refresh_instrument(inst):
    inst.state = inst.get_state()
    inst.channels_state = inst.get_channels_state()
    inst.measured_voltages = inst.measure_voltage()
    inst.measured_currents = inst.measure_current()
    inst.temperature = inst.get_temperature()
    inst.serial = inst.get_serial()
    inst.range = inst.get_range()


def refresh_screen(term, sel_col, sel_row):
    global lines

    for inst in elo._instruments:
        row = 0
        for line in lines:
            selected = row == sel_row and inst.column == sel_col
            if not line["channel"] or line["channel"] in inst.channels:
                text = line["on_show"](inst, selected, line["channel"])
                print(term.move_yx(line["y"], inst.col_pos) +
                      term.center(text, width=inst.col_width, fillchar =' '), end='')
            if line["on_enter"]:
                row += 1


if __name__ == '__main__':
    visa_name = 'GPIB::22::INSTR'

    try:
        elo = Elo(visa_name)
        elo.init()
    except pyelo.errors.VISAError:
        print("VISA error")
        exit(-1)

    sel_col = 0
    sel_row = 0
    term_width = 0
    term_height = 0

    for inst in elo._instruments:
        refresh_instrument(inst)

    term = Terminal()
    with term.fullscreen(), term.hidden_cursor():
        val = ''
        while True:

            with term.hidden_cursor():

                with term.cbreak():
                    refresh_index = 0

                    if term.width != term_width or term.height != term_height:
                        setup_screen()
                        term_width = term.width
                        term_height = term.height

                    while True:
                        val = term.inkey(timeout=0.02)
                        if not val:
                            now = perf_counter()
                            if error_display_time and now - error_display_time>10:
                                error_display_time = None
                                show_error(term)

                            if elo.error:
                                error_code, error_text = elo.read_error()
                                show_error(term, error_code, error_text)

                            try:
                                refresh_instrument(elo._instruments[refresh_index])
                            except pyelo.EloError as error:
                                show_error(term, error.error_code, error.error_text)
                            refresh_index += 1
                            if refresh_index >= len(elo._instruments):
                                refresh_index = 0

                            refresh_screen(term, sel_col, sel_row)
                        elif val.lower() == 'q':
                            break
                        elif val == 'A':
                            elo.turn_on(wait=False, delay=0.05)
                        elif val == 'a':
                            elo.turn_off(wait=False)
                        elif val.isnumeric():
                            col = int(val)-1
                            if col < len(elo._instruments):
                                sel_col = int(val)-1
                        elif val == ' ':
                            break
                        elif val.is_sequence:
                            if val.code == term.KEY_LEFT:
                                if sel_col > 0:
                                    sel_col -= 1
                                else:
                                    sel_col = len(elo._instruments) - 1
                                if sel_row > elo._instruments[sel_col].max_row:
                                    sel_row = elo._instruments[sel_col].max_row
                            elif val.code == term.KEY_RIGHT:
                                if sel_col < len(elo._instruments)-1:
                                    sel_col += 1
                                else:
                                    sel_col = 0
                                if sel_row > elo._instruments[sel_col].max_row:
                                    sel_row = elo._instruments[sel_col].max_row
                            elif val.code == term.KEY_UP:
                                if sel_row > 0:
                                    sel_row -= 1
                            elif val.code == term.KEY_DOWN:
                                if sel_row < elo._instruments[sel_col].max_row:
                                    sel_row += 1
                            elif val.code == term.KEY_ENTER:
                                break

            if val.lower() == 'q':
                break
            elif val.code == term.KEY_ENTER or val == ' ':
                channel = int((sel_row-3)/2)+1
                row = 0
                for line in lines:
                    if line["on_enter"]:
                        inst = elo._instruments[sel_col]
                        if sel_row == row:
                            print(term.move_yx(line["y"], inst.col_pos + int(inst.col_width/2-10/2)), end='')
                            try:
                                line["on_enter"](inst, channel)
                            except pyelo.EloError as error:
                                show_error(term, error.error_code, error.error_text)
                            break
                        else:
                            row += 1
